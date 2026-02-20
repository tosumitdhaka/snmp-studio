"""
api/routers/mibs.py
~~~~~~~~~~~~~~~~~~~
MIB file management + stats wiring.

Fixes:
  IMPR-11 : filename sanitization in save_mib_file()
  Part-B  : simulator restart on reload uses _restart_simulator_with_stats()
             so restart_count + simulator_run_seconds are always tracked.
             Trap restart on reload uses stored port/community/resolve_mibs.
"""

import os
import asyncio
import logging
import pathlib
import tempfile
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.mib_service import get_mib_service
from services.sim_manager import SimulatorManager
from services.trap_manager import trap_manager
from core.config import settings
from core import stats_store
from core.ws_manager import manager

router = APIRouter(prefix="/mibs", tags=["MIB Manager"])
logger = logging.getLogger(__name__)


class MibValidationResult(BaseModel):
    filename: str
    mib_name: str
    valid: bool
    imports: List[str] = []
    missing_deps: List[str] = []
    errors: List[str] = []


class BatchValidationResponse(BaseModel):
    files: List[MibValidationResult]
    global_missing_deps: List[str] = []
    can_upload: bool


# ==================== Helper Functions ====================

def save_mib_file(file: UploadFile) -> str:
    """Save uploaded MIB file with filename sanitization (IMPR-11)."""
    try:
        safe_name = pathlib.Path(file.filename).name
        if not safe_name or safe_name != file.filename:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filename '{file.filename}'. Directory traversal not allowed."
            )
        os.makedirs(settings.MIB_DIR, exist_ok=True)
        file_path = os.path.join(settings.MIB_DIR, safe_name)
        with open(file_path, 'wb') as f:
            content = file.file.read()
            f.write(content)
        logger.info(f"Saved MIB file: {safe_name}")
        return safe_name
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save MIB file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


def delete_mib_file(filename: str) -> bool:
    try:
        file_path = os.path.join(settings.MIB_DIR, filename)
        if not os.path.exists(file_path):
            return False
        os.remove(file_path)
        logger.info(f"Deleted MIB file: {filename}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete MIB file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


def list_mib_files() -> List[str]:
    try:
        if not os.path.exists(settings.MIB_DIR):
            return []
        return sorted([
            f for f in os.listdir(settings.MIB_DIR)
            if f.endswith(('.mib', '.txt', '.my'))
        ])
    except Exception as e:
        logger.error(f"Failed to list MIB files: {e}")
        return []


def _reload_dependents(sim_was_running: bool, trap_was_running: bool) -> dict:
    """
    Part B: restart simulator and trap receiver after a MIB reload.
    Uses shared stats helper for simulator, stored settings for trap manager.
    Returns status strings for both.
    """
    # Import here to avoid circular import at module load time
    from api.routers.simulator import _restart_simulator_with_stats

    sim_msg  = "Simulator not running"
    trap_msg = "Trap receiver not running"

    if sim_was_running:
        _restart_simulator_with_stats()
        sim_msg = "Simulator restarted"

    if trap_was_running:
        # Use stored _port, _community, resolve_mibs — not defaults
        trap_manager.stop()
        trap_manager.start(
            port=trap_manager._port,
            community=trap_manager._community,
            resolve_mibs=trap_manager.resolve_mibs
        )
        trap_msg = "Trap receiver restarted"

    return {"simulator": sim_msg, "trap_receiver": trap_msg}


def _mibs_summary() -> dict:
    """
    Compact MIB summary for WS broadcasts.
    Uses MibService.get_status() which includes per-module 'traps' counts.
    """
    status = get_mib_service().get_status()
    mibs   = status.get("mibs", []) or []
    return {
        "loaded":          status.get("loaded", 0),
        "failed":          status.get("failed", 0),
        "total":           status.get("total", status.get("loaded", 0) + status.get("failed", 0)),
        "traps_available": sum(m.get("traps", 0) for m in mibs),
    }


def _broadcast_mibs() -> None:
    """Fire-and-forget WS broadcast after any MIB state change."""
    asyncio.create_task(manager.broadcast({"type": "mibs", "mibs": _mibs_summary()}))


# ==================== Endpoints ====================

@router.get("/status")
def get_mib_status():
    return get_mib_service().get_status()


@router.get("/list")
def list_mibs():
    return {"mibs": list_mib_files()}


@router.post("/validate-batch")
async def validate_batch(files: List[UploadFile] = File(...)):
    mib_service = get_mib_service()
    temp_dir    = tempfile.mkdtemp(prefix="mib_validation_")
    try:
        temp_files = {}
        for file in files:
            content   = await file.read()
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_files[file.filename] = temp_path

        batch_mibs  = {}
        for filename, temp_path in temp_files.items():
            validation = mib_service.validate_mib_file(temp_path)
            batch_mibs[validation["mib_name"]] = filename

        results        = []
        global_missing = set()
        for filename, temp_path in temp_files.items():
            validation    = mib_service.validate_mib_file(temp_path)
            truly_missing = []
            for dep in validation["missing_deps"]:
                if dep in batch_mibs: continue
                if dep in mib_service.loaded_mibs: continue
                if dep in mib_service.mib_builder.mibSymbols: continue
                if mib_service._is_standard_mib(dep): continue
                truly_missing.append(dep)
                global_missing.add(dep)
            results.append(MibValidationResult(
                filename=filename,
                mib_name=validation["mib_name"],
                valid=len(validation["errors"]) == 0,
                imports=validation["imports"],
                missing_deps=truly_missing,
                errors=validation["errors"]
            ))
        return BatchValidationResponse(
            files=results,
            global_missing_deps=sorted(list(global_missing)),
            can_upload=all(r.valid for r in results)
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/upload")
async def upload_mibs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results     = []
    files_saved = 0
    try:
        for file in files:
            try:
                filename = save_mib_file(file)
                results.append({"filename": filename, "status": "saved",
                                 "mib_name": filename.rsplit('.', 1)[0]})
                files_saved += 1
            except Exception as e:
                logger.error(f"Failed to save {file.filename}: {e}")
                results.append({"filename": file.filename, "status": "error", "error": str(e)})

        sim_was_running  = SimulatorManager.status().get("running", False)
        trap_was_running = trap_manager.get_status().get("running", False)

        mib_service = get_mib_service()
        mib_service.reload()
        stats_store.increment("mibs", "reload_count")
        if files_saved > 0:
            stats_store.increment("mibs", "upload_count", by=files_saved)

        for result in results:
            if result["status"] != "saved":
                continue
            mib_name = result["mib_name"]
            if mib_name in mib_service.loaded_mibs:
                result["status"] = "loaded"
                result["objects"] = mib_service.loaded_mibs[mib_name].objects_count
                result["traps"]   = mib_service.loaded_mibs[mib_name].traps_count
            elif mib_name in mib_service.failed_mibs:
                result["status"] = "failed"
                result["error"]  = mib_service.failed_mibs[mib_name].error_message
            else:
                result["status"] = "unknown"
                result["error"]  = "MIB not found after reload"

        dep_msgs = _reload_dependents(sim_was_running, trap_was_running)
        _broadcast_mibs()
        return {"results": results, **dep_msgs}

    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reload")
async def reload_mibs():
    try:
        sim_was_running  = SimulatorManager.status().get("running", False)
        trap_was_running = trap_manager.get_status().get("running", False)

        mib_service = get_mib_service()
        mib_service.reload()
        stats_store.increment("mibs", "reload_count")

        status   = mib_service.get_status()
        dep_msgs = _reload_dependents(sim_was_running, trap_was_running)

        _broadcast_mibs()
        return {
            "status": "reloaded",
            "loaded": status["loaded"],
            "failed": status["failed"],
            **dep_msgs
        }
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{filename}")
async def delete_mib(filename: str):
    if delete_mib_file(filename):
        stats_store.increment("mibs", "delete_count")
        get_mib_service().reload()
        _broadcast_mibs()
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/traps")
def list_all_traps():
    return {"traps": get_mib_service().list_traps()}


@router.get("/objects")
def list_all_objects(module: str = None):
    return {"objects": get_mib_service().list_objects(module)}


@router.get("/resolve")
def resolve_oid(oid: str, mode: str = "name"):
    mib_service = get_mib_service()
    logger.info(f"Resolving OID: {oid}, mode: {mode}")
    try:
        result = mib_service.resolve_oid(oid, mode)
        return {"input": oid, "output": result, "mode": mode}
    except Exception as e:
        logger.error(f"Resolution failed: {e}")
        return {"input": oid, "output": oid, "mode": mode, "error": str(e)}

import os
import logging
import tempfile
import shutil
from typing import List, Set
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.mib_service import get_mib_service
from services.file_service import FileService
from services.sim_manager import SimulatorManager
from services.trap_manager import trap_manager
from core.config import settings

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

@router.get("/status")
def get_mib_status():
    """Get overall MIB service status"""
    mib_service = get_mib_service()
    return mib_service.get_status()

@router.get("/list")
def list_mibs():
    """List all MIB files"""
    return {"mibs": FileService.list_mibs()}

@router.post("/validate-batch")
async def validate_batch(files: List[UploadFile] = File(...)):
    """Validate multiple MIB files as a batch"""
    mib_service = get_mib_service()
    temp_dir = tempfile.mkdtemp(prefix="mib_validation_")
    
    try:
        temp_files = {}
        for file in files:
            content = await file.read()
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, 'wb') as f:
                f.write(content)
            temp_files[file.filename] = temp_path
        
        batch_mibs = {}
        all_imports = {}
        
        for filename, temp_path in temp_files.items():
            validation = mib_service.validate_mib_file(temp_path)
            mib_name = validation["mib_name"]
            imports = validation["imports"]
            
            batch_mibs[mib_name] = filename
            all_imports[filename] = imports
        
        results = []
        global_missing = set()
        
        for filename, temp_path in temp_files.items():
            validation = mib_service.validate_mib_file(temp_path)
            
            truly_missing = []
            for dep in validation["missing_deps"]:
                if dep in batch_mibs:
                    continue
                
                if dep in mib_service.loaded_mibs:
                    continue
                
                if dep in mib_service.mib_builder.mibSymbols:
                    continue
                
                if mib_service._is_standard_mib(dep):
                    continue
                
                truly_missing.append(dep)
                global_missing.add(dep)
            
            result = MibValidationResult(
                filename=filename,
                mib_name=validation["mib_name"],
                valid=len(validation["errors"]) == 0,
                imports=validation["imports"],
                missing_deps=truly_missing,
                errors=validation["errors"]
            )
            results.append(result)
        
        can_upload = all(r.valid for r in results)
        
        return BatchValidationResponse(
            files=results,
            global_missing_deps=sorted(list(global_missing)),
            can_upload=can_upload
        )
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/upload")
async def upload_mibs(files: List[UploadFile] = File(...)):
    """Upload multiple MIB files"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    try:
        for file in files:
            try:
                filename = await FileService.save_mib(file)
                results.append({
                    "filename": filename,
                    "status": "saved",
                    "mib_name": filename.rsplit('.', 1)[0]
                })
            except Exception as e:
                logger.error(f"Failed to save {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
        
        mib_service = get_mib_service()
        mib_service.reload()
        
        for result in results:
            if result["status"] != "saved":
                continue
            
            mib_name = result["mib_name"]
            
            if mib_name in mib_service.loaded_mibs:
                result["status"] = "loaded"
                mib_info = mib_service.loaded_mibs[mib_name]
                result["objects"] = mib_info.objects_count
                result["traps"] = mib_info.traps_count
            elif mib_name in mib_service.failed_mibs:
                result["status"] = "failed"
                mib_info = mib_service.failed_mibs[mib_name]
                result["error"] = mib_info.error_message
            else:
                result["status"] = "unknown"
                result["error"] = "MIB not found after reload"
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload")
def reload_mibs():
    """Reload all MIBs"""
    try:
        mib_service = get_mib_service()
        mib_service.reload()
        
        sim_status = SimulatorManager.status()
        if sim_status.get("running"):
            SimulatorManager.restart()
            sim_msg = "Simulator restarted"
        else:
            sim_msg = "Simulator not running"
        
        trap_status = trap_manager.get_status()
        if trap_status.get("running"):
            trap_manager.stop()
            trap_manager.start()
            trap_msg = "Trap receiver restarted"
        else:
            trap_msg = "Trap receiver not running"
        
        status = mib_service.get_status()
        
        return {
            "status": "reloaded",
            "loaded": status["loaded"],
            "failed": status["failed"],
            "simulator": sim_msg,
            "trap_receiver": trap_msg
        }
    
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
def delete_mib(filename: str):
    """Delete a MIB file"""
    if FileService.delete_mib(filename):
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")

@router.get("/traps")
def list_all_traps():
    """List all available traps"""
    mib_service = get_mib_service()
    return {"traps": mib_service.list_traps()}

@router.get("/objects")
def list_all_objects(module: str = None):
    """List all MIB objects"""
    mib_service = get_mib_service()
    return {"objects": mib_service.list_objects(module)}

@router.get("/resolve")
def resolve_oid(oid: str, mode: str = "name"):
    """Resolve OID"""
    mib_service = get_mib_service()
    result = mib_service.resolve_oid(oid, mode)
    return {"input": oid, "output": result, "mode": mode}

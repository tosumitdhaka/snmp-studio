"""
api/routers/simulator.py
~~~~~~~~~~~~~~~~~~~~~~~~
Simulator lifecycle endpoints + custom data management.
Stats are persisted to stats.json via stats_store.

Fixes in this version:
  BUG-8  : restart() preserves saved port/community (via sim_manager)
  BUG-12 : single restart code path
  Part-B : _restart_simulator_with_stats() shared helper — used by this
           router AND mibs.py so indirect restarts are always tracked
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.sim_manager import SimulatorManager
from core.config import settings
from core import stats_store

router = APIRouter(prefix="/simulator", tags=["Simulator"])
logger = logging.getLogger(__name__)


class SimConfig(BaseModel):
    port: Optional[int] = None
    community: Optional[str] = None


# ---------------------------------------------------------------------------
# Module-level start-time tracker
# In-memory only — resets on container restart.
# Used exclusively for delta calculation of simulator_run_seconds.
# ---------------------------------------------------------------------------
_sim_start_time: Optional[datetime] = None


def set_sim_start_time() -> None:
    """Seed _sim_start_time to now. Called by lifespan auto-start and tests."""
    global _sim_start_time
    _sim_start_time = datetime.now(timezone.utc)


def _record_stop_stats() -> None:
    """Accumulate elapsed run time and increment stop_count atomically."""
    global _sim_start_time
    elapsed = 0
    if _sim_start_time:
        elapsed = int((datetime.now(timezone.utc) - _sim_start_time).total_seconds())
        _sim_start_time = None
    s = stats_store.load()
    stats_store.update_module("simulator", {
        "stop_count":            s["simulator"]["stop_count"] + 1,
        "simulator_run_seconds": s["simulator"]["simulator_run_seconds"] + elapsed,
    })


def _restart_simulator_with_stats() -> dict:
    """
    Part B: shared restart helper used by:
      - POST /simulator/restart  (endpoint)
      - POST /simulator/data     (conditional restart after data update)
      - POST /mibs/reload        (conditional restart after MIB reload)

    Ensures _sim_start_time and restart_count are always updated regardless
    of which code path triggers the restart.
    """
    _record_stop_stats()          # stop leg: accumulate run time
    time.sleep(0.5)
    result = SimulatorManager.restart()
    if result.get("status") == "started":
        set_sim_start_time()      # start leg: seed new start time
        stats_store.increment("simulator", "restart_count")
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status():
    status = SimulatorManager.status()
    if status.get("running") and _sim_start_time:
        delta = datetime.now(timezone.utc) - _sim_start_time
        status["uptime"] = str(delta).split(".")[0]
    else:
        status["uptime"] = None
    return status


@router.post("/start")
def start_simulator(config: SimConfig = None):
    global _sim_start_time
    p = config.port      if config else None
    c = config.community if config else None

    current = SimulatorManager.status()
    if current.get("running"):
        return {
            "status":    "already_running",
            "message":   "Simulator is already running",
            "pid":       current.get("pid"),
            "port":      current.get("port"),
            "community": current.get("community"),
        }

    result = SimulatorManager.start(port=p, community=c)
    if result.get("status") == "started":
        set_sim_start_time()
        stats_store.increment("simulator", "start_count")
        return {
            "status":    "started",
            "message":   "Simulator started successfully",
            "pid":       result.get("pid"),
            "port":      result.get("port"),
            "community": result.get("community"),
        }
    return result


@router.post("/stop")
def stop_simulator():
    result = SimulatorManager.stop()
    if result.get("status") == "stopped":
        _record_stop_stats()
        return {"status": "stopped", "message": "Simulator stopped successfully"}
    return result


@router.post("/restart")
def restart_simulator():
    result = _restart_simulator_with_stats()
    if result.get("status") == "started":
        return {
            "status":    "restarted",
            "message":   "Simulator restarted successfully",
            "pid":       result.get("pid"),
            "port":      result.get("port"),
            "community": result.get("community"),
        }
    return result


@router.get("/data")
def get_custom_data():
    try:
        if not settings.CUSTOM_DATA_FILE.exists():
            return {}
        with open(settings.CUSTOM_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data")
def update_custom_data(data: dict):
    """Save custom OID data. If simulator is running, restart it with stats tracking."""
    try:
        os.makedirs(settings.CUSTOM_DATA_FILE.parent, exist_ok=True)
        with open(settings.CUSTOM_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        if SimulatorManager.status().get("running"):
            # Part B fix: use shared helper so restart_count + run_seconds are tracked
            _restart_simulator_with_stats()
            msg = "Data saved and simulator restarted"
        else:
            msg = "Data saved (simulator is currently stopped)"

        logger.info(f"Custom data updated: {len(data)} entries")
        return {"status": "saved", "message": msg}
    except Exception as e:
        logger.error(f"Failed to save custom data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

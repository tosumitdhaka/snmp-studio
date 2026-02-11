import os
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.sim_manager import SimulatorManager
from core.config import settings

router = APIRouter(prefix="/simulator", tags=["Simulator"])
logger = logging.getLogger(__name__)

class SimConfig(BaseModel):
    port: int = None
    community: str = None

# Custom Data File Path
CUSTOM_DATA_FILE = os.path.join(settings.BASE_DIR, "data", "configs", "custom_data.json")

# Simulator Metrics (in-memory storage)
_simulator_metrics = {
    "start_time": None,
    "requests": 0,
    "last_activity": None,
}


def _mark_activity():
    """Mark simulator activity and increment request counter"""
    _simulator_metrics["requests"] += 1
    _simulator_metrics["last_activity"] = datetime.now(timezone.utc)


def _format_uptime(start_time: datetime) -> str:
    """Format uptime as human-readable string"""
    if not start_time:
        return None
    delta = datetime.now(timezone.utc) - start_time
    return str(delta).split(".")[0]


# ==================== Simulator Endpoints ====================

@router.get("/status")
def get_status():
    status = SimulatorManager.status()
    running = status.get("running", False)
    
    # Add metrics to status response
    status["uptime"] = _format_uptime(_simulator_metrics.get("start_time")) if running else None
    status["requests"] = _simulator_metrics.get("requests", 0) if running else 0
    status["last_activity"] = (
        _simulator_metrics.get("last_activity").isoformat() 
        if running and _simulator_metrics.get("last_activity") 
        else None
    )
    
    return status


@router.post("/start")
def start_simulator(config: SimConfig = None):
    p = config.port if config else None
    c = config.community if config else None
    
    # Check if already running
    current_status = SimulatorManager.status()
    if current_status.get("running"):
        return {
            "status": "already_running",
            "message": "Simulator is already running",
            "pid": current_status.get("pid"),
            "port": current_status.get("port"),
            "community": current_status.get("community")
        }
    
    result = SimulatorManager.start(port=p, community=c)
    
    if result.get("status") == "started":
        # Record metrics on successful start
        _simulator_metrics["start_time"] = datetime.now(timezone.utc)
        _mark_activity()
        
        return {
            "status": "started",
            "message": "Simulator started successfully",
            "pid": result.get("pid"),
            "port": result.get("port"),
            "community": result.get("community")
        }
    
    return result


@router.post("/stop")
def stop_simulator():
    result = SimulatorManager.stop()
    
    if result.get("status") == "stopped":
        # Clear start time on stop
        _simulator_metrics["start_time"] = None
        _mark_activity()
        
        return {
            "status": "stopped",
            "message": "Simulator stopped successfully"
        }
    
    return result


@router.post("/restart")
def restart_simulator():
    # Stop if running
    stop_result = SimulatorManager.stop()
    
    # Clear and mark activity
    _simulator_metrics["start_time"] = None
    
    import time
    time.sleep(0.5)
    
    # Start again
    start_result = SimulatorManager.start()
    
    if start_result.get("status") == "started":
        _simulator_metrics["start_time"] = datetime.now(timezone.utc)
        _mark_activity()
        
        return {
            "status": "restarted",
            "message": "Simulator restarted successfully",
            "pid": start_result.get("pid"),
            "port": start_result.get("port"),
            "community": start_result.get("community")
        }
    
    return start_result


# ==================== Custom Data Endpoints ====================

@router.get("/data")
def get_custom_data():
    """Get custom data for simulator"""
    try:
        if not os.path.exists(CUSTOM_DATA_FILE):
            return {}
        
        with open(CUSTOM_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load custom data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data")
def update_custom_data(data: dict):
    """Update custom data and restart simulator if running"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CUSTOM_DATA_FILE), exist_ok=True)
        
        # Save data
        with open(CUSTOM_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        _mark_activity()
        
        # Restart simulator if running
        sim_status = SimulatorManager.status()
        if sim_status.get("running"):
            SimulatorManager.restart()
            # Update start time after restart
            _simulator_metrics["start_time"] = datetime.now(timezone.utc)
            msg = "Data saved and simulator restarted"
        else:
            msg = "Data saved (simulator is currently stopped)"
        
        logger.info(f"Custom data updated: {len(data)} entries")
        return {"status": "saved", "message": msg}
    
    except Exception as e:
        logger.error(f"Failed to save custom data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

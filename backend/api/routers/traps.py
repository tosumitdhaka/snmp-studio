from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
import logging
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    send_notification,
    NotificationType 
)
from pysnmp.proto.rfc1902 import (
    Counter32, Gauge32, Integer32, IpAddress, OctetString, TimeTicks, ObjectIdentifier
)
from services.trap_manager import trap_manager
from services.mib_service import get_mib_service
from core.config import settings

router = APIRouter(prefix="/traps", tags=["Traps"])
logger = logging.getLogger(__name__)

class TrapVarbind(BaseModel):
    oid: str
    type: str = "String"
    value: str

class TrapSendRequest(BaseModel):
    target: str
    port: int = 162
    community: str = "public"
    oid: str
    varbinds: List[TrapVarbind] = []

class TrapStartRequest(BaseModel):
    port: int = 1162
    community: str = "public"
    resolve_mibs: bool = True

@router.post("/send")
async def send_trap(req: TrapSendRequest):
    try:
        mib_service = get_mib_service()
        
        logger.info(f"Sending trap: {req.oid} to {req.target}:{req.port}")
        
        # 1. Validate and prepare trap OID
        if "::" in req.oid:
            trap_details = mib_service.get_trap_details(req.oid)
            if not trap_details:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Trap '{req.oid}' not found in loaded MIBs. Please upload the required MIB first."
                )
            
            logger.info(f"Sending trap: {trap_details['full_name']} (OID: {trap_details['oid']})")
            trap_oid = ObjectIdentity(trap_details['oid'])
        else:
            trap_oid = ObjectIdentity(req.oid)
        
        notification = NotificationType(trap_oid)
        
        # 2. Add VarBinds
        for idx, vb in enumerate(req.varbinds):
            logger.debug(f"VarBind {idx}: {vb.oid} = {vb.value} ({vb.type})")
            
            try:
                if vb.type == "Integer": 
                    val = Integer32(int(vb.value))
                elif vb.type == "Counter": 
                    val = Counter32(int(vb.value))
                elif vb.type == "Gauge": 
                    val = Gauge32(int(vb.value))
                elif vb.type == "OID": 
                    val = ObjectIdentifier(str(vb.value))
                elif vb.type == "IpAddress": 
                    val = IpAddress(str(vb.value))
                elif vb.type == "TimeTicks": 
                    val = TimeTicks(int(vb.value))
                else: 
                    val = OctetString(str(vb.value))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid value for {vb.oid}: {vb.value} (expected {vb.type})"
                )
            
            # Resolve VarBind OID
            if "::" in vb.oid:
                numeric_oid = mib_service.resolve_oid(vb.oid, mode="numeric")
                vb_obj = ObjectIdentity(numeric_oid)
            else:
                vb_obj = ObjectIdentity(vb.oid)
            
            notification.addVarBinds(ObjectType(vb_obj, val))
        
        # 3. Send
        target = await UdpTransportTarget.create((req.target, req.port))
        
        errorIndication, errorStatus, errorIndex, varBinds = await send_notification(
            SnmpEngine(),
            CommunityData(req.community, mpModel=1),
            target,
            ContextData(),
            'trap',
            notification
        )
        
        if errorIndication:
            raise HTTPException(
                status_code=500, 
                detail=f"SNMP Error: {str(errorIndication)}"
            )
        
        if errorStatus:
            raise HTTPException(
                status_code=500,
                detail=f"SNMP Error: {errorStatus.prettyPrint()}"
            )
        
        logger.info(f"✓ Trap sent to {req.target}:{req.port}")
        return {"status": "sent", "target": req.target, "port": req.port}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trap send failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/validate-trap")
def validate_trap(oid: str):
    """Validate if a trap OID exists"""
    mib_service = get_mib_service()
    
    if "::" in oid:
        trap_details = mib_service.get_trap_details(oid)
        if trap_details:
            return {"valid": True, "trap": trap_details}
        else:
            return {
                "valid": False,
                "error": f"Trap '{oid}' not found in loaded MIBs",
                "suggestion": "Upload the required MIB in MIB Manager"
            }
    else:
        return {"valid": True, "trap": {"oid": oid}}

@router.get("/status")
def get_status(): 
    return trap_manager.get_status()

@router.post("/start")
def start_receiver(req: TrapStartRequest): 
    return trap_manager.start(req.port, req.community, req.resolve_mibs)

@router.post("/stop")
def stop_receiver(): 
    return trap_manager.stop()

@router.get("/")
def get_received_traps(limit: int = 50): 
    return {"data": trap_manager.get_traps(limit)}

@router.delete("/")
def clear_traps(): 
    trap_manager.clear_traps()
    return {"status": "cleared"}

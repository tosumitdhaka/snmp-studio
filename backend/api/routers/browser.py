import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from services.mib_service import get_mib_service

router = APIRouter(prefix="/mibs/browse", tags=["MIB Browser"])
logger = logging.getLogger(__name__)


@router.get("/modules")
def list_modules():
    """List all MIB modules with statistics"""
    try:
        mib_service = get_mib_service()
        modules = mib_service.get_module_stats()
        
        return {"modules": modules}
    
    except Exception as e:
        logger.error(f"Failed to list modules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/module")
def get_module_tree(module: Optional[str] = None):
    """
    Get tree organized by modules
    
    Args:
        module: Filter by specific module (optional)
    
    Returns:
        List of module trees with their root objects
    """
    try:
        mib_service = get_mib_service()
        tree = mib_service.get_module_tree(module)
        
        return {
            "view": "module",
            "modules": tree,
            "count": len(tree)
        }
    
    except Exception as e:
        logger.error(f"Failed to get module tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/oid")
def get_oid_tree(
    root_oid: str = Query("1.3.6.1", description="Starting OID"),
    depth: int = Query(1, ge=1, le=5, description="Expansion depth"),
    module: Optional[str] = Query(None, description="Filter by module")
):
    """
    Get OID tree starting from root_oid
    
    Args:
        root_oid: Starting OID (default: 1.3.6.1 = internet)
        depth: How many levels to expand (1-5)
        module: Filter by MIB module
    
    Returns:
        Tree structure with root and children
    """
    try:
        mib_service = get_mib_service()
        tree = mib_service.get_oid_tree(root_oid, depth, module)
        
        return tree
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get OID tree: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{oid:path}")
def get_node_details(oid: str):
    """
    Get detailed information about a specific OID node
    """
    try:
        mib_service = get_mib_service()
        details = mib_service.get_node_details(oid_identifier=oid)
        
        # If it's a notification, get associated objects
        node = details["node"]
        if node.get("type") == "NotificationType":
            # Get trap details from list_traps
            trap_details = mib_service.get_trap_details(oid)
            if trap_details:
                details["trap_objects"] = trap_details.get("objects", [])
        
        return details
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get node details for {oid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
def search_oids(
    query: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    module: Optional[str] = Query(None, description="Filter by module"),
    type_filter: Optional[str] = Query(None, description="Filter by node type")
):
    """
    Search OIDs by name, description, or numeric OID
    
    Args:
        query: Search term (minimum 2 characters)
        limit: Maximum number of results (1-500)
        module: Filter by MIB module
        type_filter: Filter by node type (MibScalar, MibTable, MibTableColumn, NotificationType, etc.)
    
    Returns:
        Search results with count
    """
    try:
        mib_service = get_mib_service()
        results = mib_service.search_oids(query, limit, module, type_filter)
        
        return results
    
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

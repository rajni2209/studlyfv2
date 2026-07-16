from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import logging
from auth_institution import get_auth_user
from db import blocked_entities_col

logger = logging.getLogger("blocked_entities_routes")

router = APIRouter(prefix="/api/v1/institution/blocked-entities", tags=["Blocked Entities"])

class BlockEntityRequest(BaseModel):
    entity_type: str = Field(..., description="Either 'candidate' or 'organization'")
    identifier: str = Field(..., description="Email or unique identifier")
    name: Optional[str] = None
    reason: str = Field(..., min_length=1)

class BlockedEntityResponse(BaseModel):
    id: str
    institution_id: str
    entity_type: str
    identifier: str
    name: Optional[str] = None
    reason: str
    blocked_at: datetime
    blocked_by_user_id: str

@router.get("/", response_model=List[BlockedEntityResponse])
async def get_blocked_entities(auth_user: dict = Depends(get_auth_user)):
    institution_id = auth_user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=403, detail="Not linked to any institution")

    cursor = blocked_entities_col.find({"institution_id": institution_id}).sort("blocked_at", -1)
    results = []
    async for doc in cursor:
        results.append({
            "id": str(doc["_id"]),
            "institution_id": doc["institution_id"],
            "entity_type": doc["entity_type"],
            "identifier": doc["identifier"],
            "name": doc.get("name"),
            "reason": doc["reason"],
            "blocked_at": doc["blocked_at"],
            "blocked_by_user_id": doc.get("blocked_by_user_id", "unknown")
        })
    return results

@router.post("/", response_model=BlockedEntityResponse)
async def block_entity(req: BlockEntityRequest, auth_user: dict = Depends(get_auth_user)):
    institution_id = auth_user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=403, detail="Not linked to any institution")

    if req.entity_type not in ["candidate", "organization"]:
        raise HTTPException(status_code=400, detail="entity_type must be candidate or organization")

    existing = await blocked_entities_col.find_one({
        "institution_id": institution_id,
        "entity_type": req.entity_type,
        "identifier": req.identifier
    })
    
    if existing:
        raise HTTPException(status_code=400, detail=f"This {req.entity_type} is already blocked.")

    doc = {
        "institution_id": institution_id,
        "entity_type": req.entity_type,
        "identifier": req.identifier,
        "name": req.name,
        "reason": req.reason,
        "blocked_at": datetime.utcnow(),
        "blocked_by_user_id": auth_user.get("user_id", "unknown")
    }

    result = await blocked_entities_col.insert_one(doc)
    
    return {
        "id": str(result.inserted_id),
        **doc
    }

@router.delete("/{entity_id}")
async def unblock_entity(entity_id: str, auth_user: dict = Depends(get_auth_user)):
    institution_id = auth_user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=403, detail="Not linked to any institution")
        
    try:
        obj_id = ObjectId(entity_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await blocked_entities_col.delete_one({
        "_id": obj_id,
        "institution_id": institution_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blocked entity not found")

    return {"status": "success", "message": "Entity unblocked successfully"}

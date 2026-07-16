from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from auth_institution import get_auth_user
from services.communication_service import CommunicationService, MessageType, SegmentationType
from bson import ObjectId

router = APIRouter(prefix="/api/v1/institution/communications", tags=["Custom Communications"])

class SegmentCountRequest(BaseModel):
    event_id: str
    segment_type: SegmentationType
    criteria: Dict[str, Any] = {}

class SendBulkMessageRequest(BaseModel):
    event_id: str
    segment_type: SegmentationType
    criteria: Dict[str, Any] = {}
    subject: str
    message_body: str
    message_type: MessageType = MessageType.BOTH

@router.post("/segment-count")
async def get_segment_count(req: SegmentCountRequest, user: dict = Depends(get_auth_user)):
    role = str(user.get("role") or "").lower()
    if role != "institution":
        raise HTTPException(status_code=403, detail="Institution access required")
    
    institution_id = user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=400, detail="User account is not linked to any institution")
        
    from db import events_col
    try:
        ev_id = ObjectId(req.event_id)
    except:
        ev_id = req.event_id
    
    event = await events_col.find_one({"$or": [{"_id": ev_id}, {"event_id": req.event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event_inst_id = str(event.get("institution_id") or event.get("createdBy") or "")
    if event_inst_id != str(institution_id):
        raise HTTPException(status_code=403, detail="This event does not belong to your institution")
        
    segment_ids = await CommunicationService.create_segment(
        institution_id=institution_id,
        event_id=req.event_id,
        segment_type=req.segment_type,
        criteria=req.criteria
    )
    return {"count": len(segment_ids)}

@router.post("/send")
async def send_bulk_message(req: SendBulkMessageRequest, user: dict = Depends(get_auth_user)):
    role = str(user.get("role") or "").lower()
    if role != "institution":
        raise HTTPException(status_code=403, detail="Institution access required")
    
    institution_id = user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=400, detail="User account is not linked to any institution")
        
    if not req.subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required")
    if not req.message_body.strip():
        raise HTTPException(status_code=400, detail="Message body is required")
        
    from db import events_col
    try:
        ev_id = ObjectId(req.event_id)
    except:
        ev_id = req.event_id
    
    event = await events_col.find_one({"$or": [{"_id": ev_id}, {"event_id": req.event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    event_inst_id = str(event.get("institution_id") or event.get("createdBy") or "")
    if event_inst_id != str(institution_id):
        raise HTTPException(status_code=403, detail="This event does not belong to your institution")
        
    segment_ids = await CommunicationService.create_segment(
        institution_id=institution_id,
        event_id=req.event_id,
        segment_type=req.segment_type,
        criteria=req.criteria
    )
    
    if not segment_ids:
        raise HTTPException(status_code=400, detail="No participants match the selected filters.")
        
    result = await CommunicationService.send_bulk_message(
        institution_id=institution_id,
        event_id=req.event_id,
        segment_ids=segment_ids,
        subject=req.subject,
        message_body=req.message_body,
        message_type=req.message_type
    )
    
    return result

@router.get("/history")
async def get_history(event_id: Optional[str] = None, limit: int = 50, user: dict = Depends(get_auth_user)):
    role = str(user.get("role") or "").lower()
    if role != "institution":
        raise HTTPException(status_code=403, detail="Institution access required")
    
    institution_id = user.get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=400, detail="User account is not linked to any institution")
        
    history = await CommunicationService.get_communication_history(
        institution_id=institution_id,
        event_id=event_id,
        limit=limit
    )
    return history

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class MessageSchema(BaseModel):
    role: str
    content: str
    timestamp: str
    duration_sec: float = 0.0

class SessionCreate(BaseModel):
    session_id: str
    title: Optional[str] = None
    started_at: str
    ended_at: str
    total_duration_sec: float
    user_speech_duration_sec: float
    messages: List[MessageSchema]
    scenario_place: Optional[str] = None
    scenario_partner: Optional[str] = None
    scenario_goal: Optional[str] = None
    scenario_state_json: Optional[Dict[str, Any]] = None
    scenario_completed_at: Optional[str] = None
    deleted: Optional[bool] = None

class SessionResponse(SessionCreate):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


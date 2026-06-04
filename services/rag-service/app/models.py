from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)
    latitude: float = Field(default=3.8667)
    longitude: float = Field(default=11.5167)


class ChatResponse(BaseModel):
    answer: str
    question: str
    location_detected: Optional[str] = None
    created_at: datetime


class ChatHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    location_detected: Optional[str] = None
    created_at: datetime
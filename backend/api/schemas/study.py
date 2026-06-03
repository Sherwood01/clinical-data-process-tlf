"""Pydantic schemas for Study API."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class StudyCreate(BaseModel):
    name: str = Field(..., max_length=500)
    protocol_id: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class StudyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None


class StudyResponse(BaseModel):
    id: UUID
    name: str
    protocol_id: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

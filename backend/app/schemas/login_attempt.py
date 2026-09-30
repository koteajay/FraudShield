"""Pydantic schemas for LoginAttempt entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginAttemptBase(BaseModel):
    """Base schema for authentication telemetry."""
    attempted_email: str = Field(..., max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    country: Optional[str] = Field(None, max_length=3)
    city: Optional[str] = Field(None, max_length=64)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_successful: bool = Field(default=False)
    failure_reason: Optional[str] = Field(None, max_length=128)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    is_suspicious: bool = Field(default=False)


class LoginAttemptCreate(LoginAttemptBase):
    """Schema for logging an authentication attempt."""
    user_id: Optional[str] = None
    device_id: Optional[str] = None


class LoginAttemptResponse(LoginAttemptBase):
    """Response schema for login attempt."""
    id: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

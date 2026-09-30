"""Pydantic schemas for Notification entity."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import NotificationType, NotificationSeverity, NotificationChannel


class NotificationBase(BaseModel):
    """Base schema for notification alert."""
    notification_type: NotificationType
    title: str = Field(..., max_length=128)
    message: str
    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP)
    severity: NotificationSeverity = Field(default=NotificationSeverity.INFO)
    metadata_json: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    user_id: str
    transaction_id: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Response schema for notification."""
    id: str
    user_id: str
    transaction_id: Optional[str] = None
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

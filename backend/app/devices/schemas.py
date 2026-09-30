"""Pydantic schemas for Device API requests and responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DeviceResponse(BaseModel):
    """Public representation of a registered user device."""

    id: str = Field(..., description="Internal device UUID")
    user_id: Optional[str] = Field(default=None, description="Owner user ID")
    device_id: str = Field(..., description="Application-level client device identifier")
    browser: Optional[str] = Field(default="Unknown", description="Detected browser")
    operating_system: Optional[str] = Field(default="Unknown", description="Detected operating system")
    device_type: str = Field(default="unknown", description="Form factor (desktop, mobile, tablet, etc.)")
    ip_address: Optional[str] = Field(default=None, description="Last observed IP address")
    is_trusted: bool = Field(default=False, description="Whether device is marked as trusted")
    first_seen_at: datetime = Field(..., description="First observed timestamp")
    last_seen_at: datetime = Field(..., description="Most recent observed timestamp")

    model_config = ConfigDict(from_attributes=True)


class DeviceCreateRequest(BaseModel):
    """Payload to register or check a client device."""

    device_id: Optional[str] = Field(default=None, description="Client persistent device identifier")
    user_agent: Optional[str] = Field(default=None, description="Browser User-Agent header")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    device_type: Optional[str] = Field(default=None, description="Optional override for device form factor")
    is_trusted: bool = Field(default=False, description="Initial trust designation")


class DeviceCheckResponse(BaseModel):
    """Device recognition and novelty check result."""

    user_id: str
    device_id: str
    is_known: bool
    is_new_device: bool
    device: DeviceResponse

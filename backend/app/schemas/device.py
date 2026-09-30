"""Pydantic schemas for Device entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    """Base schema for device hardware and telemetry."""
    fingerprint: str = Field(..., max_length=128, description="Cryptographic device fingerprint hash")
    device_type: str = Field(default="unknown", max_length=50, description="Device form factor")
    operating_system: Optional[str] = Field(None, max_length=50, description="Operating system")
    browser: Optional[str] = Field(None, max_length=50, description="Web browser name")
    user_agent: Optional[str] = Field(None, description="Raw User-Agent string")
    ip_address: Optional[str] = Field(None, max_length=45, description="Client IP address")
    is_trusted: bool = Field(default=False, description="Trusted device flag")
    is_vpn: bool = Field(default=False, description="VPN detection signal")
    is_tor: bool = Field(default=False, description="Tor network detection signal")
    is_emulator: bool = Field(default=False, description="Emulator detection signal")


class DeviceCreate(DeviceBase):
    """Schema for registering or attaching a device."""
    user_id: Optional[str] = Field(None, description="Optional associated user ID")


class DeviceResponse(DeviceBase):
    """Response schema for device telemetry."""
    id: str
    user_id: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

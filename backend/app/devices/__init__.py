"""Device identification and fingerprinting module."""

from app.devices.metadata import (
    DeviceMetadata,
    extract_device_metadata,
    parse_browser,
    parse_operating_system,
    parse_device_type,
)
from app.devices.service import DeviceService
from app.devices.schemas import (
    DeviceResponse,
    DeviceCreateRequest,
    DeviceCheckResponse,
)

__all__ = [
    "DeviceMetadata",
    "extract_device_metadata",
    "parse_browser",
    "parse_operating_system",
    "parse_device_type",
    "DeviceService",
    "DeviceResponse",
    "DeviceCreateRequest",
    "DeviceCheckResponse",
]

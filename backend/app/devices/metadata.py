"""Device metadata extraction and User-Agent parsing."""

import re
import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DeviceMetadata(BaseModel):
    """Normalized software device metadata extracted from HTTP headers and client telemetry."""

    device_id: str = Field(..., description="Software/Application device identifier (e.g. UUID)")
    browser: str = Field(default="Unknown", description="Detected browser name")
    operating_system: str = Field(default="Unknown", description="Detected operating system")
    device_type: str = Field(default="unknown", description="Form factor (desktop, mobile, tablet, unknown)")
    user_agent: Optional[str] = Field(default=None, description="Raw HTTP User-Agent string")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")

    model_config = ConfigDict(frozen=True)


def parse_browser(user_agent: Optional[str]) -> str:
    """
    Lightweight, deterministic browser detection from User-Agent string.
    Zero external dependencies.
    """
    if not user_agent or not isinstance(user_agent, str):
        return "Unknown"

    ua = user_agent.strip()

    # Note: Edge includes "Edg/" or "Edge/"
    if "Edg/" in ua or "Edge/" in ua:
        return "Edge"
    # Opera includes "OPR/" or "Opera/"
    if "OPR/" in ua or "Opera/" in ua:
        return "Opera"
    # Firefox includes "Firefox/" or "FxiOS/"
    if "Firefox/" in ua or "FxiOS/" in ua:
        return "Firefox"
    # Chrome includes "Chrome/" or "CriOS/" (must check after Edge & Opera)
    if "Chrome/" in ua or "CriOS/" in ua or "Chromium/" in ua:
        return "Chrome"
    # Safari includes "Safari/" and version/webkit without Chrome
    if "Safari/" in ua and ("Version/" in ua or "AppleWebKit/" in ua):
        return "Safari"

    return "Unknown"


def parse_operating_system(user_agent: Optional[str]) -> str:
    """
    Lightweight, deterministic operating system detection from User-Agent string.
    Zero external dependencies.
    """
    if not user_agent or not isinstance(user_agent, str):
        return "Unknown"

    ua = user_agent.strip()

    # iOS must precede macOS (iOS UA contains "like Mac OS X")
    if any(k in ua for k in ["iPhone", "iPad", "iPod", "CPU iPhone OS", "CPU OS"]):
        return "iOS"
    # Android must precede Linux (Android UA contains "Linux; Android")
    if "Android" in ua:
        return "Android"
    # Windows
    if "Windows NT" in ua or "Windows" in ua or "Win64" in ua or "Win32" in ua:
        return "Windows"
    # macOS
    if "Macintosh" in ua or "Mac OS X" in ua or "macOS" in ua:
        return "macOS"
    # Linux
    if "Linux" in ua or "X11" in ua:
        return "Linux"

    return "Unknown"


def parse_device_type(user_agent: Optional[str]) -> str:
    """Infer general device form factor (mobile, tablet, desktop, unknown)."""
    if not user_agent or not isinstance(user_agent, str):
        return "unknown"

    ua = user_agent.lower()

    if "tablet" in ua or "ipad" in ua:
        return "tablet"
    if "mobile" in ua or "iphone" in ua or "ipod" in ua or "android" in ua:
        return "mobile"
    if any(k in ua for k in ["windows", "macintosh", "mac os x", "linux", "x11"]):
        return "desktop"

    return "unknown"


def extract_device_metadata(
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_id: Optional[str] = None,
) -> DeviceMetadata:
    """
    Extract and normalize device metadata from client-provided headers and parameters.
    If no device_id is presented, a fallback UUID is generated.
    """
    resolved_device_id = str(device_id).strip() if device_id else str(uuid.uuid4())
    browser = parse_browser(user_agent)
    operating_system = parse_operating_system(user_agent)
    device_type = parse_device_type(user_agent)

    return DeviceMetadata(
        device_id=resolved_device_id,
        browser=browser,
        operating_system=operating_system,
        device_type=device_type,
        user_agent=user_agent.strip() if user_agent else None,
        ip_address=ip_address.strip() if ip_address else None,
    )

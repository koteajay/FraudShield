"""Device management service for tracking, registering, and identifying client devices."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.logging_config import logger
from app.models.device import Device
from app.models.user import User
from app.devices.metadata import DeviceMetadata, extract_device_metadata


class DeviceService:
    """
    Core service managing user devices, known/new device detection,
    and device telemetry refresh.
    """

    def __init__(self, db: Session):
        self.db = db

    def find_device(self, user_id: str, device_id: str) -> Optional[Device]:
        """
        Look up a registered device for a user by device_id or fingerprint.
        """
        if not user_id or not device_id:
            return None

        clean_device_id = str(device_id).strip()
        stmt = (
            select(Device)
            .where(
                Device.user_id == user_id,
                or_(
                    Device.device_id == clean_device_id,
                    Device.fingerprint == clean_device_id,
                    Device.id == clean_device_id,
                ),
            )
        )
        return self.db.scalars(stmt).first()

    def is_known_device(self, user_id: str, device_id: str) -> bool:
        """
        Determine whether a device has been previously registered/seen for a user.
        """
        return self.find_device(user_id, device_id) is not None

    def get_user_devices(self, user_id: str) -> List[Device]:
        """
        Retrieve all devices historically associated with a user, sorted newest first.
        """
        stmt = (
            select(Device)
            .where(Device.user_id == user_id)
            .order_by(Device.last_seen_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def register_device(
        self,
        user_id: str,
        metadata: DeviceMetadata,
        is_trusted: bool = False,
        is_vpn: bool = False,
        is_tor: bool = False,
        is_emulator: bool = False,
    ) -> Device:
        """
        Register a newly observed device for a user.
        Preserves first_seen_at = last_seen_at = now.
        """
        now = datetime.now(timezone.utc)
        device = Device(
            user_id=user_id,
            device_id=metadata.device_id,
            fingerprint=metadata.device_id,
            browser=metadata.browser,
            operating_system=metadata.operating_system,
            device_type=metadata.device_type,
            user_agent=metadata.user_agent,
            ip_address=metadata.ip_address,
            is_trusted=is_trusted,
            is_vpn=is_vpn,
            is_tor=is_tor,
            is_emulator=is_emulator,
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)

        logger.info(
            f"Registered new device for user={user_id}: device_id={device.device_id}, "
            f"os={device.operating_system}, browser={device.browser}"
        )
        return device

    def update_last_seen(
        self,
        device: Device,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Device:
        """
        Update the last_seen_at and telemetry for an existing device.
        Never resets first_seen_at.
        """
        now = datetime.now(timezone.utc)
        device.last_seen_at = now
        device.updated_at = now

        if ip_address:
            device.ip_address = ip_address
        if user_agent:
            device.user_agent = user_agent

        self.db.commit()
        self.db.refresh(device)

        logger.debug(
            f"Updated last_seen for device_id={device.device_id} (user={device.user_id})"
        )
        return device

    def get_or_create_device(
        self,
        user_id: str,
        metadata: DeviceMetadata,
    ) -> Tuple[Device, bool]:
        """
        Check if device is known. If known, refresh last_seen; otherwise register new.
        Returns: (Device, is_new_device)
        """
        existing = self.find_device(user_id, metadata.device_id)
        if existing:
            updated = self.update_last_seen(
                existing,
                ip_address=metadata.ip_address,
                user_agent=metadata.user_agent,
            )
            return updated, False

        new_device = self.register_device(user_id, metadata)
        return new_device, True

    def process_incoming_request(
        self,
        user_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Tuple[Device, bool]:
        """
        Convenience flow: extract metadata from request -> lookup/register device -> return device & is_new flag.
        """
        metadata = extract_device_metadata(
            user_agent=user_agent,
            ip_address=ip_address,
            device_id=device_id,
        )
        return self.get_or_create_device(user_id, metadata)

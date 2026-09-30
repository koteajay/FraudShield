"""User, Device, and LoginAttempt Repositories."""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.user import User
from app.models.device import Device
from app.models.login_attempt import LoginAttempt
from app.models.enums import UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entities."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Lookup user by lowercase trimmed email."""
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        return self.db.scalars(stmt).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Lookup user by username."""
        stmt = select(User).where(func.lower(User.username) == username.lower().strip())
        return self.db.scalars(stmt).first()

    def update_risk_score(self, user_id: str, new_risk_score: float) -> Optional[User]:
        """Update aggregate user baseline risk rating."""
        user = self.get(user_id)
        if user:
            user.risk_score = max(0.0, min(100.0, new_risk_score))
            self.db.commit()
            self.db.refresh(user)
        return user


class DeviceRepository(BaseRepository[Device]):
    """Data access repository for Device fingerprint telemetry."""

    def __init__(self, db: Session):
        super().__init__(Device, db)

    def get_by_fingerprint(self, fingerprint: str) -> Optional[Device]:
        """Lookup device record by client fingerprint hash."""
        stmt = select(Device).where(Device.fingerprint == fingerprint)
        return self.db.scalars(stmt).first()

    def list_by_user(self, user_id: str) -> List[Device]:
        """Retrieve all devices linked to a specific user account."""
        stmt = select(Device).where(Device.user_id == user_id).order_by(Device.last_seen_at.desc())
        return list(self.db.scalars(stmt).all())

    def record_or_update(
        self,
        fingerprint: str,
        user_id: Optional[str] = None,
        device_type: str = "unknown",
        operating_system: Optional[str] = None,
        browser: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        is_vpn: bool = False,
        is_tor: bool = False,
        is_emulator: bool = False,
    ) -> Device:
        """Find existing device by fingerprint or create a new one, refreshing telemetry."""
        device = self.get_by_fingerprint(fingerprint)
        if device:
            if user_id and not device.user_id:
                device.user_id = user_id
            if operating_system:
                device.operating_system = operating_system
            if browser:
                device.browser = browser
            if user_agent:
                device.user_agent = user_agent
            if ip_address:
                device.ip_address = ip_address
            device.is_vpn = is_vpn or device.is_vpn
            device.is_tor = is_tor or device.is_tor
            device.is_emulator = is_emulator or device.is_emulator
            device.last_seen_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(device)
            return device
        else:
            new_device = Device(
                fingerprint=fingerprint,
                user_id=user_id,
                device_type=device_type,
                operating_system=operating_system,
                browser=browser,
                user_agent=user_agent,
                ip_address=ip_address,
                is_vpn=is_vpn,
                is_tor=is_tor,
                is_emulator=is_emulator,
            )
            return self.create(new_device)


class LoginAttemptRepository(BaseRepository[LoginAttempt]):
    """Data access repository for Authentication telemetry and velocity."""

    def __init__(self, db: Session):
        super().__init__(LoginAttempt, db)

    def list_by_user(self, user_id: str, limit: int = 50) -> List[LoginAttempt]:
        """Fetch chronological login history for a user."""
        stmt = (
            select(LoginAttempt)
            .where(LoginAttempt.user_id == user_id)
            .order_by(LoginAttempt.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_failed_attempts(
        self,
        attempted_email: str,
        since_minutes: int = 15,
    ) -> int:
        """Count failed authentication attempts within a sliding time window for an email."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                func.lower(LoginAttempt.attempted_email) == attempted_email.lower().strip(),
                LoginAttempt.is_successful.is_(False),
                LoginAttempt.timestamp >= cutoff,
            )
        )
        return self.db.scalar(stmt) or 0

"""Device Database Model."""

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.login_attempt import LoginAttempt


class Device(Base):
    """Device entity capturing application device IDs, browser telemetry, and threat signals."""

    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_user_device", "user_id", "device_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique internal device UUID",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional user associated with this device",
    )
    device_id: Mapped[str] = mapped_column(
        String(128),
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        doc="Application-level client device identifier",
    )
    fingerprint: Mapped[str] = mapped_column(
        String(128),
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        doc="Client hardware/browser canvas/audio cryptographic hash",
    )
    device_type: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
        nullable=False,
        doc="Device form factor (desktop, mobile, tablet, bot, etc.)",
    )
    operating_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="OS identifier and version",
    )
    browser: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Browser engine/name and version",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Full HTTP User-Agent string",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        doc="Originating IPv4 or IPv6 address",
    )
    is_trusted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this device is marked as explicitly trusted by user/analyst",
    )
    is_vpn: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether device IP resolves to a known VPN service",
    )
    is_tor: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether device IP is an active Tor exit node",
    )
    is_emulator: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether device exhibits virtualized/emulator characteristics",
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of first interaction",
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of most recent interaction",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Record update timestamp",
    )

    def __init__(self, **kwargs):
        # Synchronize device_id and fingerprint for backwards compatibility
        if "device_id" in kwargs and "fingerprint" not in kwargs:
            kwargs["fingerprint"] = kwargs["device_id"]
        elif "fingerprint" in kwargs and "device_id" not in kwargs:
            kwargs["device_id"] = kwargs["fingerprint"]
        if "device_type" not in kwargs:
            kwargs["device_type"] = "unknown"
        if "is_trusted" not in kwargs:
            kwargs["is_trusted"] = False
        if "is_vpn" not in kwargs:
            kwargs["is_vpn"] = False
        if "is_tor" not in kwargs:
            kwargs["is_tor"] = False
        if "is_emulator" not in kwargs:
            kwargs["is_emulator"] = False
        super().__init__(**kwargs)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="devices",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="device",
    )
    login_attempts: Mapped[List["LoginAttempt"]] = relationship(
        "LoginAttempt",
        back_populates="device",
    )

    def __repr__(self) -> str:
        return f"<Device id={self.id} fingerprint={self.fingerprint[:8]} type={self.device_type}>"

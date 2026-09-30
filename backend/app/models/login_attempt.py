"""LoginAttempt Database Model."""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device


class LoginAttempt(Base):
    """
    Authentication attempt telemetry record.
    Used for detecting brute force, credential stuffing, anomalous geolocations, and compromised accounts.
    """

    __tablename__ = "login_attempts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique login attempt identifier",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Matched user ID if account exists, otherwise NULL",
    )
    attempted_email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
        doc="Email address or username supplied during authentication",
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Associated client device record, if identified",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        index=True,
        nullable=True,
        doc="Source IPv4 or IPv6 address",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="HTTP User-Agent header value",
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        doc="Resolved country ISO 3166 code",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Resolved city name",
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Geographic latitude coordinate",
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Geographic longitude coordinate",
    )
    is_successful: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
        doc="True if authentication credentials were valid and session issued",
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        doc="Reason code for failed authentication (e.g. INVALID_PASSWORD, ACCOUNT_LOCKED, MFA_FAILED)",
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Calculated authentication risk score (0.0 - 100.0)",
    )
    is_suspicious: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
        doc="Flag indicating suspicious telemetry (e.g. velocity spike, unknown country)",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Timestamp when authentication request was received",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="login_attempts",
    )
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="login_attempts",
    )

    def __repr__(self) -> str:
        return f"<LoginAttempt id={self.id} email={self.attempted_email} success={self.is_successful}>"

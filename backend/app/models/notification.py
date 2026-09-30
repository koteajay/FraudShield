"""Notification Database Model."""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, TYPE_CHECKING
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import NotificationType, NotificationSeverity, NotificationChannel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class Notification(Base):
    """
    Security alert or transactional notification dispatched to a user or compliance team.
    Supports in-app badges, SMS, email, and audit trails.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique notification identifier",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Recipient user identifier",
    )
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Associated transaction, if alert was transaction-triggered",
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        SQLEnum(NotificationType, native_enum=False, length=40),
        index=True,
        nullable=False,
        doc="Alert type classification (SUSPICIOUS_TRANSACTION, NEW_DEVICE, etc.)",
    )
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Brief notification title summary",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed body message text",
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SQLEnum(NotificationChannel, native_enum=False, length=20),
        default=NotificationChannel.IN_APP,
        nullable=False,
        doc="Target dispatch channel (IN_APP, EMAIL, SMS, PUSH, WEBHOOK)",
    )
    severity: Mapped[NotificationSeverity] = mapped_column(
        SQLEnum(NotificationSeverity, native_enum=False, length=20),
        default=NotificationSeverity.INFO,
        nullable=False,
        doc="Alert criticality level",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
        doc="Whether recipient marked notification as viewed",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Arbitrary structured payload, deep links, or event data",
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Dispatch timestamp",
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp marked as read",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Record creation timestamp",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
    )
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.notification_type} user={self.user_id} read={self.is_read}>"

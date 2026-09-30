"""User Database Model."""

import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Float, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.device import Device
    from app.models.login_attempt import LoginAttempt
    from app.models.review import Review
    from app.models.notification import Notification


class User(Base):
    """User account entity storing identity, profile, and baseline risk."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique user identifier (UUID)",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique email address",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique username handle",
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Full legal name",
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="E.164 phone number",
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Hashed credentials",
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False, length=20),
        default=UserRole.USER,
        nullable=False,
        doc="User role (user, analyst, admin)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is active",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user has verified identity/email",
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Aggregated baseline user risk score (0.0 - 100.0)",
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
        doc="Last update timestamp",
    )

    # Relationships
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Transaction.timestamp.desc()",
    )
    devices: Mapped[List["Device"]] = relationship(
        "Device",
        back_populates="user",
    )
    login_attempts: Mapped[List["LoginAttempt"]] = relationship(
        "LoginAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="LoginAttempt.timestamp.desc()",
    )
    assigned_reviews: Mapped[List["Review"]] = relationship(
        "Review",
        foreign_keys="Review.assigned_to_user_id",
        back_populates="assigned_to",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Notification.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"

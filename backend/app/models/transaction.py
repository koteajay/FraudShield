"""Transaction Database Model."""

import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from sqlalchemy import (
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import RiskLevel, TransactionStatus, ReviewStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device
    from app.models.fraud_flag import FraudFlag
    from app.models.fraud_rule_result import FraudRuleResult
    from app.models.review import Review
    from app.models.notification import Notification


class Transaction(Base):
    """
    Transaction entity recording financial transfer details, telemetry,
    risk evaluation, location, merchant, and disposition status.
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique internal transaction UUID",
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: f"TXN-{uuid.uuid4().hex[:12].upper()}",
        doc="Public/External transaction reference identifier",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Owner/Sender user ID",
    )
    device_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Originating device ID",
    )

    # Core Financial Information
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Transaction amount value",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="ISO 4217 3-letter currency code",
    )
    payment_method: Mapped[str] = mapped_column(
        String(50),
        default="credit_card",
        nullable=False,
        doc="Payment vehicle (credit_card, debit_card, crypto, wire, etc.)",
    )
    payment_card_bin: Mapped[Optional[str]] = mapped_column(
        String(8),
        nullable=True,
        doc="Card Bank Identification Number (first 6-8 digits)",
    )
    payment_card_last4: Mapped[Optional[str]] = mapped_column(
        String(4),
        nullable=True,
        doc="Last four digits of payment card",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Transaction purpose or line-item description",
    )

    # Merchant Information
    merchant_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        doc="Merchant account or identifier",
    )
    merchant_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        doc="Legal or trade name of merchant",
    )
    merchant_category: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Merchant Category Code (MCC) or business industry label",
    )

    # Location Information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        index=True,
        nullable=True,
        doc="Originating IP address during transaction",
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        doc="Origin country ISO code",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Origin city name",
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
    billing_country: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        doc="Cardholder billing address country ISO code",
    )
    shipping_country: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        doc="Physical goods destination country ISO code",
    )
    is_billing_shipping_mismatch: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True if billing country diverges from delivery country",
    )
    distance_from_last_txn_km: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Physical displacement distance (km) from previous transaction",
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Timestamp when transaction was authorized or submitted",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Record ingestion timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last modification timestamp",
    )

    # Risk Scoring & Assessment
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        index=True,
        nullable=False,
        doc="Calculated aggregate fraud risk score (0.0 - 100.0)",
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        SQLEnum(RiskLevel, native_enum=False, length=20),
        default=RiskLevel.LOW,
        index=True,
        nullable=False,
        doc="Binned risk rating (LOW, MEDIUM, HIGH, CRITICAL)",
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus, native_enum=False, length=20),
        default=TransactionStatus.APPROVED,
        index=True,
        nullable=False,
        doc="Gateway execution status",
    )

    # Review Lifecycle Status
    review_status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, native_enum=False, length=25),
        default=ReviewStatus.NOT_REQUIRED,
        index=True,
        nullable=False,
        doc="Current review queue state",
    )

    # Extra Extensible Payload
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Flexible JSON metadata for ML features, raw gateway responses, etc.",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="transactions",
    )
    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="transactions",
    )
    fraud_flags: Mapped[List["FraudFlag"]] = relationship(
        "FraudFlag",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="FraudFlag.created_at.desc()",
    )
    rule_results: Mapped[List["FraudRuleResult"]] = relationship(
        "FraudRuleResult",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="FraudRuleResult.created_at.desc()",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="Review.created_at.desc()",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="transaction",
    )

    def __repr__(self) -> str:
        return f"<Transaction ref={self.transaction_reference} amount={self.amount} {self.currency} risk={self.risk_score} level={self.risk_level}>"

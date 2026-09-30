"""FraudFlag Database Model."""

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
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import FlagSeverity

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class FraudFlag(Base):
    """
    Specific anomaly or suspicious condition raised against a transaction.
    Provides explainable markers for human analysts and ML pipelines.
    """

    __tablename__ = "fraud_flags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique fraud flag identifier",
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Target transaction associated with this flag",
    )
    flag_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        doc="Machine-readable flag category (e.g. VELOCITY_BURST, HIGH_RISK_GEO, IMPOSSIBLE_TRAVEL)",
    )
    severity: Mapped[FlagSeverity] = mapped_column(
        SQLEnum(FlagSeverity, native_enum=False, length=20),
        default=FlagSeverity.MEDIUM,
        index=True,
        nullable=False,
        doc="Severity weight (LOW, MEDIUM, HIGH, CRITICAL)",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed human-readable explanation of why this flag was triggered",
    )
    score_impact: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Numerical penalty added to transaction risk score by this flag",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this flag is actively considered in scoring",
    )
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether flag has been reviewed or dismissed",
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Analyst user ID or automated process that resolved the flag",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of resolution",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Timestamp when flag was raised",
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="fraud_flags",
    )

    def __repr__(self) -> str:
        return f"<FraudFlag id={self.id} type={self.flag_type} severity={self.severity} impact=+{self.score_impact}>"

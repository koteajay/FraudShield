"""FraudRuleResult Database Model."""

import uuid
from datetime import datetime
from typing import Optional, Any, Dict, TYPE_CHECKING
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
from app.models.enums import FlagSeverity

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class FraudRuleResult(Base):
    """
    Evaluation record for an individual rule executed against a transaction.
    Provides complete auditability of which heuristic or deterministic rules evaluated and triggered.
    """

    __tablename__ = "fraud_rule_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique rule evaluation result ID",
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Transaction ID against which rule executed",
    )
    rule_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
        doc="Standard rule identifier (e.g. RULE_GEO_SPEED_VIOLATION)",
    )
    rule_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-friendly rule title",
    )
    rule_category: Mapped[str] = mapped_column(
        String(64),
        default="GENERAL",
        nullable=False,
        doc="Rule domain (VELOCITY, GEO, DEVICE, PAYMENT, IDENTITY, BEHAVIORAL)",
    )
    is_triggered: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        nullable=False,
        doc="True if condition matched and triggered a risk action",
    )
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        doc="Configured rule weight factor in aggregate risk formula",
    )
    severity: Mapped[FlagSeverity] = mapped_column(
        SQLEnum(FlagSeverity, native_enum=False, length=20),
        default=FlagSeverity.MEDIUM,
        nullable=False,
        doc="Rule risk impact classification",
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Evaluation context parameters, threshold comparisons, and measured metrics",
    )
    execution_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Rule evaluation latency in milliseconds",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Execution timestamp",
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="rule_results",
    )

    def __repr__(self) -> str:
        return f"<FraudRuleResult rule={self.rule_id} triggered={self.is_triggered} severity={self.severity}>"

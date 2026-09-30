"""Review Database Model."""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    String,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import ReviewState, ReviewDecision, ReviewPriority

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.user import User


class Review(Base):
    """
    Manual review case assigned to a fraud analyst.
    Enables case investigation, notes, escalation, and audit trail of human decisions.
    """

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique review case identifier",
    )
    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Transaction under manual review",
    )
    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="Fraud analyst currently assigned to this case",
    )
    status: Mapped[ReviewState] = mapped_column(
        SQLEnum(ReviewState, native_enum=False, length=20),
        default=ReviewState.ASSIGNED,
        index=True,
        nullable=False,
        doc="Workflow phase (ASSIGNED, IN_PROGRESS, APPROVED, REJECTED, ESCALATED, CLOSED)",
    )
    decision: Mapped[Optional[ReviewDecision]] = mapped_column(
        SQLEnum(ReviewDecision, native_enum=False, length=30),
        nullable=True,
        doc="Formal disposition reached by investigator",
    )
    priority: Mapped[ReviewPriority] = mapped_column(
        SQLEnum(ReviewPriority, native_enum=False, length=20),
        default=ReviewPriority.MEDIUM,
        index=True,
        nullable=False,
        doc="Review urgency queue ranking (LOW, MEDIUM, HIGH, URGENT)",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Analyst investigation commentary and findings",
    )
    resolution_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Formal justification explaining the final decision",
    )
    escalated_to: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Senior analyst, compliance team, or supervisor ID escalated to",
    )
    # Reviewer workflow audit fields (Phase 12)
    reviewer_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        index=True,
        nullable=True,
        default="reviewer-demo",
        doc="Identifier of the reviewer recording the action",
    )
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="Previous review status prior to transition",
    )
    new_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="New review status after transition",
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Reviewer investigation notes",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Timestamp review case opened",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp case was last touched",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when final decision was recorded",
    )

    # Relationships
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="reviews",
    )
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        back_populates="assigned_reviews",
    )

    def __repr__(self) -> str:
        return f"<Review id={self.id} txn={self.transaction_id} status={self.status} priority={self.priority}>"

"""Transaction, FraudFlag, FraudRuleResult, and Review Repositories."""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, desc
from app.models.transaction import Transaction
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.review import Review
from app.models.enums import TransactionStatus, ReviewStatus, RiskLevel, ReviewState
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    """Data access repository for Transactions and fraud detection queries."""

    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_by_reference(self, reference: str) -> Optional[Transaction]:
        """Fetch transaction by unique external/public reference."""
        stmt = select(Transaction).where(Transaction.transaction_reference == reference)
        return self.db.scalars(stmt).first()

    def get_with_details(self, transaction_id: str) -> Optional[Transaction]:
        """Fetch transaction with all associated flags, rules, and reviews eagerly loaded."""
        stmt = (
            select(Transaction)
            .where(Transaction.id == transaction_id)
            .options(
                selectinload(Transaction.fraud_flags),
                selectinload(Transaction.rule_results),
                selectinload(Transaction.reviews),
                selectinload(Transaction.user),
                selectinload(Transaction.device),
            )
        )
        return self.db.scalars(stmt).first()

    def list_by_user(self, user_id: str, limit: int = 50) -> List[Transaction]:
        """List transactions belonging to a specific user in reverse chronological order."""
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_high_risk(self, min_risk_score: float = 70.0, limit: int = 50) -> List[Transaction]:
        """List high risk or critical transactions."""
        stmt = (
            select(Transaction)
            .where(Transaction.risk_score >= min_risk_score)
            .order_by(Transaction.risk_score.desc(), Transaction.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_pending_review(self, limit: int = 50) -> List[Transaction]:
        """Fetch transactions awaiting analyst action."""
        stmt = (
            select(Transaction)
            .where(Transaction.review_status.in_([ReviewStatus.PENDING_REVIEW, ReviewStatus.IN_REVIEW]))
            .order_by(Transaction.risk_score.desc(), Transaction.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_user_last_transaction(self, user_id: str, before_time: Optional[datetime] = None) -> Optional[Transaction]:
        """Fetch the most recent transaction for a user prior to a given timestamp."""
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        if before_time:
            stmt = stmt.where(Transaction.timestamp < before_time)
        stmt = stmt.order_by(Transaction.timestamp.desc()).limit(1)
        return self.db.scalars(stmt).first()

    def count_user_transactions_in_window(self, user_id: str, minutes: int = 60) -> int:
        """Count how many transactions user made in the past N minutes (velocity analysis)."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        stmt = (
            select(func.count())
            .select_from(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.timestamp >= cutoff,
            )
        )
        return self.db.scalar(stmt) or 0

    def sum_user_amount_in_window(self, user_id: str, minutes: int = 60) -> float:
        """Sum total currency spend by user in the past N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        stmt = (
            select(func.coalesce(func.sum(Transaction.amount), 0.0))
            .where(
                Transaction.user_id == user_id,
                Transaction.timestamp >= cutoff,
            )
        )
        return float(self.db.scalar(stmt) or 0.0)


class FraudFlagRepository(BaseRepository[FraudFlag]):
    """Data access repository for Fraud Flags."""

    def __init__(self, db: Session):
        super().__init__(FraudFlag, db)

    def list_by_transaction(self, transaction_id: str) -> List[FraudFlag]:
        """Retrieve all flags attached to a transaction."""
        stmt = (
            select(FraudFlag)
            .where(FraudFlag.transaction_id == transaction_id)
            .order_by(FraudFlag.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())


class FraudRuleResultRepository(BaseRepository[FraudRuleResult]):
    """Data access repository for Fraud Rule Results."""

    def __init__(self, db: Session):
        super().__init__(FraudRuleResult, db)

    def list_by_transaction(self, transaction_id: str) -> List[FraudRuleResult]:
        """Retrieve all executed rule results for a transaction."""
        stmt = (
            select(FraudRuleResult)
            .where(FraudRuleResult.transaction_id == transaction_id)
            .order_by(FraudRuleResult.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_triggered_by_transaction(self, transaction_id: str) -> List[FraudRuleResult]:
        """Retrieve only triggered rule results for a transaction."""
        stmt = (
            select(FraudRuleResult)
            .where(
                FraudRuleResult.transaction_id == transaction_id,
                FraudRuleResult.is_triggered.is_(True),
            )
            .order_by(FraudRuleResult.severity.desc())
        )
        return list(self.db.scalars(stmt).all())


class ReviewRepository(BaseRepository[Review]):
    """Data access repository for Analyst Reviews."""

    def __init__(self, db: Session):
        super().__init__(Review, db)

    def list_by_analyst(self, analyst_id: str, state: Optional[ReviewState] = None) -> List[Review]:
        """List reviews assigned to an analyst."""
        stmt = select(Review).where(Review.assigned_to_user_id == analyst_id)
        if state:
            stmt = stmt.where(Review.status == state)
        stmt = stmt.order_by(Review.priority.desc(), Review.created_at.asc())
        return list(self.db.scalars(stmt).all())

    def list_open_queue(self) -> List[Review]:
        """List unassigned or in-progress reviews."""
        stmt = (
            select(Review)
            .where(Review.status.in_([ReviewState.ASSIGNED, ReviewState.IN_PROGRESS]))
            .order_by(Review.priority.desc(), Review.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

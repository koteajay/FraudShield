"""Transaction Velocity Fraud Rule."""

from datetime import datetime, timedelta, timezone
from typing import Any
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


def _parse_timestamp(ts: Any) -> datetime:
    """Parse or ensure timezone-aware datetime."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.now(timezone.utc)


class TransactionVelocityRule(FraudRule):
    """
    Detects high transaction frequency exceeding configured thresholds
    within a sliding time window.
    """

    @property
    def rule_id(self) -> str:
        return "transaction_velocity"

    @property
    def name(self) -> str:
        return "Transaction Velocity"

    @property
    def description(self) -> str:
        return "Flags rapid successive transactions within a brief time window."

    @property
    def default_score_contribution(self) -> float:
        return 25.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        threshold_count = int(context.get_config_value("VELOCITY_THRESHOLD_COUNT", 5))
        window_minutes = int(context.get_config_value("VELOCITY_WINDOW_MINUTES", 5))

        current_time = _parse_timestamp(context.get_transaction_timestamp())
        window_start = current_time - timedelta(minutes=window_minutes)

        # Gather transactions within the time window
        matching_count = 0
        current_id = context.get_transaction_field("id")

        included_current = False
        for txn in context.recent_transactions:
            txn_id = _safe_get(txn, "id")
            txn_time = _parse_timestamp(_safe_get(txn, "timestamp"))

            if txn_id and current_id and txn_id == current_id:
                included_current = True

            # Match within sliding window up to current transaction time
            if window_start <= txn_time <= current_time:
                matching_count += 1

        # If current transaction wasn't in recent_transactions list, include it
        if not included_current:
            matching_count += 1

        triggered = matching_count > threshold_count
        if triggered:
            reason = (
                f"More than {threshold_count} transactions occurred within "
                f"{window_minutes} minutes ({matching_count} detected)."
            )
            score = self.default_score_contribution
        else:
            reason = (
                f"Transaction velocity is normal ({matching_count} transactions within "
                f"{window_minutes} minutes; threshold is {threshold_count})."
            )
            score = 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "transaction_count": matching_count,
                "window_minutes": window_minutes,
                "threshold": threshold_count,
            },
            score_contribution=score,
        )

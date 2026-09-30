"""Multiple Failed Login Fraud Rule."""

from datetime import datetime, timedelta, timezone
from typing import Any
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


def _parse_ts(ts: Any) -> datetime:
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


class MultipleFailedLoginRule(FraudRule):
    """
    Detects repeated failed authentication attempts preceding a transaction,
    indicating possible credential stuffing, account takeover, or brute force.
    """

    @property
    def rule_id(self) -> str:
        return "multiple_failed_login"

    @property
    def name(self) -> str:
        return "Multiple Failed Login"

    @property
    def description(self) -> str:
        return "Flags transactions preceded by multiple failed authentication attempts within a sliding time window."

    @property
    def default_score_contribution(self) -> float:
        return 20.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        threshold = int(context.get_config_value("FAILED_LOGIN_THRESHOLD", 3))
        window_minutes = int(context.get_config_value("FAILED_LOGIN_WINDOW_MINUTES", 10))

        current_time = _parse_ts(context.get_transaction_timestamp())
        window_start = current_time - timedelta(minutes=window_minutes)

        failed_count = 0
        failure_reasons = []

        for attempt in context.login_attempts:
            is_successful = bool(_safe_get(attempt, "is_successful", False))
            attempt_time = _parse_ts(_safe_get(attempt, "timestamp"))

            if not is_successful and window_start <= attempt_time <= current_time:
                failed_count += 1
                reason = _safe_get(attempt, "failure_reason")
                if reason and reason not in failure_reasons:
                    failure_reasons.append(reason)

        triggered = failed_count >= threshold
        if triggered:
            reason = (
                f"{failed_count} failed login attempts occurred within the past "
                f"{window_minutes} minutes (threshold: {threshold})."
            )
            score = self.default_score_contribution
        else:
            reason = (
                f"Failed login count ({failed_count}) within {window_minutes} minutes "
                f"is below the alert threshold ({threshold})."
            )
            score = 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "failed_login_count": failed_count,
                "window_minutes": window_minutes,
                "threshold": threshold,
                "failure_reasons": failure_reasons,
            },
            score_contribution=score,
        )

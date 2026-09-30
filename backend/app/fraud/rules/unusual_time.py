"""Unusual Time Fraud Rule."""

from datetime import datetime, timezone
from typing import Any, List, Optional, Set, Tuple
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


def _extract_time_info(
    ts: Any,
    tz_name: Optional[str] = None,
) -> Tuple[int, int, str]:
    """
    Extract (hour, minute, formatted_hh_mm) with timezone awareness.
    If tz_name is provided, attempts conversion via ZoneInfo.
    """
    dt: Optional[datetime] = None
    if isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            dt = None

    if dt is None:
        dt = datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Apply timezone conversion if requested
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            dt = dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass

    return dt.hour, dt.minute, f"{dt.hour:02d}:{dt.minute:02d}"


def _build_normal_hours_set(start_h: int, end_h: int, buffer_hours: int = 0) -> Set[int]:
    """
    Construct the set of valid hours (0-23) for a normal window,
    properly supporting overnight spans crossing midnight (e.g. 22:00 to 04:00).
    """
    if start_h <= end_h:
        # Continuous within same day (e.g. 08:00 to 22:00)
        return {h % 24 for h in range(start_h - buffer_hours, end_h + buffer_hours + 1)}
    else:
        # Overnight window crossing midnight (e.g. 22:00 to 04:00)
        evening = {h % 24 for h in range(start_h - buffer_hours, 24)}
        morning = {h % 24 for h in range(0, end_h + buffer_hours + 1)}
        return evening | morning


class UnusualTimeRule(FraudRule):
    """
    Detects transactions occurring outside of a user's established historical
    active hours of the day, with overnight window and timezone support.
    """

    @property
    def rule_id(self) -> str:
        return "unusual_time"

    @property
    def name(self) -> str:
        return "Unusual Transaction Time"

    @property
    def description(self) -> str:
        return "Flags transactions initiated at hours that deviate from normal user behavioral patterns."

    @property
    def default_score_contribution(self) -> float:
        return 10.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        min_history = int(context.get_config_value("UNUSUAL_TIME_MIN_HISTORY", 5))
        buffer_hours = int(context.get_config_value("UNUSUAL_TIME_BUFFER_HOURS", 1))

        # Check for explicitly missing timestamp
        raw_ts = context.get_transaction_field("timestamp")
        if raw_ts is None and getattr(context.current_transaction, "timestamp", None) is None:
            # If current_transaction dictionary literally omits timestamp
            if isinstance(context.current_transaction, dict) and "timestamp" not in context.current_transaction:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    triggered=False,
                    reason="Transaction does not contain a timestamp.",
                    evidence={"status": "missing_timestamp"},
                    score_contribution=0.0,
                )

        current_time = context.get_transaction_timestamp()
        tz_override = context.get_transaction_field("timezone") or _safe_get(context.user, "timezone")
        current_hour, current_minute, formatted_time = _extract_time_info(current_time, tz_override)
        current_id = context.get_transaction_field("id")

        # 1. Profile-driven evaluation (preferred Phase 5/7 flow)
        profile = getattr(context, "user_profile", None)
        if profile is not None:
            sample_size = getattr(profile, "profile_transaction_count", 0)
            start_h = getattr(profile, "normal_transaction_start_hour", None)
            end_h = getattr(profile, "normal_transaction_end_hour", None)

            if sample_size < min_history or start_h is None or end_h is None:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    triggered=False,
                    reason="Insufficient historical data to establish the user's normal transaction hours.",
                    evidence={
                        "current_hour": current_hour,
                        "transaction_time": formatted_time,
                        "historical_count": sample_size,
                        "required_minimum": min_history,
                        "profile_status": str(getattr(profile, "profile_status", "INSUFFICIENT_DATA")),
                        "outside_normal_hours": False,
                    },
                    score_contribution=0.0,
                )

            # Determine whether current hour is within normal window (supporting overnight spans)
            normal_hours_set = _build_normal_hours_set(start_h, end_h, buffer_hours=buffer_hours)
            is_normal = current_hour in normal_hours_set
            triggered = not is_normal

            if triggered:
                reason = (
                    f"Transaction initiated at {formatted_time} is outside the user's "
                    f"regular activity hours ({start_h:02d}:00–{end_h:02d}:00)."
                )
                score = self.default_score_contribution
            else:
                reason = (
                    f"Transaction hour ({formatted_time}) is consistent with the user's "
                    f"active time window ({start_h:02d}:00–{end_h:02d}:00)."
                )
                score = 0.0

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=triggered,
                reason=reason,
                evidence={
                    "current_hour": current_hour,
                    "transaction_time": formatted_time,
                    "normal_start": f"{start_h:02d}:00",
                    "normal_end": f"{end_h:02d}:00",
                    "historical_min_hour": start_h,
                    "historical_max_hour": end_h,
                    "buffer_hours": buffer_hours,
                    "outside_normal_hours": triggered,
                    "sample_size": sample_size,
                },
                score_contribution=score,
            )

        # 2. Raw historical transaction hours fallback (Phase 3 fallback)
        historical_hours: List[int] = []
        for txn in context.historical_transactions:
            txn_id = _safe_get(txn, "id")
            if txn_id and current_id and txn_id == current_id:
                continue
            ts = _safe_get(txn, "timestamp")
            if ts is not None:
                h, _, _ = _extract_time_info(ts, tz_override)
                historical_hours.append(h)

        if len(historical_hours) < min_history:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="Insufficient historical transactions to establish a temporal baseline.",
                evidence={
                    "current_hour": current_hour,
                    "transaction_time": formatted_time,
                    "historical_count": len(historical_hours),
                    "required_minimum": min_history,
                    "outside_normal_hours": False,
                },
                score_contribution=0.0,
            )

        # Circular distance to nearest historical hour
        min_circular_dist = min(
            min((current_hour - h) % 24, (h - current_hour) % 24)
            for h in historical_hours
        )
        hist_min = min(historical_hours)
        hist_max = max(historical_hours)
        triggered = min_circular_dist > buffer_hours

        if triggered:
            reason = (
                f"Transaction initiated at {formatted_time} is outside the user's "
                f"regular activity hours ({hist_min:02d}:00–{hist_max:02d}:00)."
            )
            score = self.default_score_contribution
        else:
            reason = (
                f"Transaction hour ({formatted_time}) is consistent with the user's "
                f"active time window ({hist_min:02d}:00–{hist_max:02d}:00)."
            )
            score = 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "current_hour": current_hour,
                "transaction_time": formatted_time,
                "normal_start": f"{hist_min:02d}:00",
                "normal_end": f"{hist_max:02d}:00",
                "historical_min_hour": hist_min,
                "historical_max_hour": hist_max,
                "buffer_hours": buffer_hours,
                "distance_from_window_hours": min_circular_dist,
                "outside_normal_hours": triggered,
                "sample_size": len(historical_hours),
            },
            score_contribution=score,
        )

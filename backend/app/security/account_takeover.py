"""Account Takeover (ATO) correlation and detection service."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from app.logging_config import logger
from app.models.enums import RiskLevel
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult
from app.security.models import (
    AccountTakeoverAssessment,
    SignalStatus,
)

# Standardized ATO signal identifiers
SIGNAL_NEW_DEVICE = "new_device"
SIGNAL_NEW_LOCATION = "new_location"
SIGNAL_UNUSUAL_TIME = "unusual_time"
SIGNAL_FAILED_LOGIN = "failed_login"
SIGNAL_UNUSUAL_TRANSACTION = "unusual_transaction"

SIGNAL_LABELS = {
    SIGNAL_NEW_DEVICE: "new device",
    SIGNAL_NEW_LOCATION: "unusual or new location",
    SIGNAL_UNUSUAL_TIME: "unusual transaction time",
    SIGNAL_FAILED_LOGIN: "failed login activity",
    SIGNAL_UNUSUAL_TRANSACTION: "unusually large transaction amount",
}


class AccountTakeoverDetector:
    """
    Correlation and detection layer analyzing compound risk patterns for potential
    account compromise. Correlates 5 distinct signals from rule results and telemetry.
    Does NOT replace individual fraud rules or the Phase 4 overall risk score.
    """

    def evaluate(
        self,
        context: RuleContext,
        rule_results: Optional[List[RuleResult]] = None,
    ) -> AccountTakeoverAssessment:
        """
        Evaluate account takeover risk by correlating individual rule outputs and context.
        """
        results = rule_results or []
        rule_map: Dict[str, RuleResult] = {r.rule_id: r for r in results}

        user_id = str(
            context.get_transaction_field("user_id")
            or _safe_get(context.user, "id")
            or "unknown_user"
        )
        transaction_id = str(context.get_transaction_field("id") or "") or None

        evidence: Dict[str, Any] = {}
        statuses: Dict[str, SignalStatus] = {}

        # -------------------------------------------------------------------
        # 1. New Device Signal
        # -------------------------------------------------------------------
        if "device_change" in rule_map:
            dev_res = rule_map["device_change"]
            if dev_res.evidence.get("status") == "missing_device_telemetry":
                statuses[SIGNAL_NEW_DEVICE] = SignalStatus.UNKNOWN
            elif dev_res.triggered:
                statuses[SIGNAL_NEW_DEVICE] = SignalStatus.TRUE
                evidence[SIGNAL_NEW_DEVICE] = dev_res.evidence
            else:
                statuses[SIGNAL_NEW_DEVICE] = SignalStatus.FALSE
        else:
            # Fall back to inspecting context directly
            curr_dev = context.current_device or context.get_transaction_field("device_id")
            prof = getattr(context, "user_profile", None)
            if curr_dev and prof and hasattr(prof, "known_device_ids"):
                dev_id = str(getattr(curr_dev, "device_id", curr_dev))
                if dev_id in prof.known_device_ids:
                    statuses[SIGNAL_NEW_DEVICE] = SignalStatus.FALSE
                else:
                    statuses[SIGNAL_NEW_DEVICE] = SignalStatus.TRUE
                    evidence[SIGNAL_NEW_DEVICE] = {"device_id": dev_id}
            else:
                statuses[SIGNAL_NEW_DEVICE] = SignalStatus.UNKNOWN

        # -------------------------------------------------------------------
        # 2. New Location Signal
        # -------------------------------------------------------------------
        if "impossible_geographical_location" in rule_map and rule_map["impossible_geographical_location"].triggered:
            statuses[SIGNAL_NEW_LOCATION] = SignalStatus.TRUE
            evidence[SIGNAL_NEW_LOCATION] = rule_map["impossible_geographical_location"].evidence
        elif "device_change" in rule_map and rule_map["device_change"].evidence.get("new_device_new_location"):
            statuses[SIGNAL_NEW_LOCATION] = SignalStatus.TRUE
            evidence[SIGNAL_NEW_LOCATION] = rule_map["device_change"].evidence
        else:
            curr_city = context.get_transaction_field("city") or context.get_transaction_field("location_city")
            curr_country = context.get_transaction_field("country") or context.get_transaction_field("location_country")
            prof = getattr(context, "user_profile", None)

            if curr_city or curr_country:
                known_locs = []
                if prof and getattr(prof, "known_locations", None):
                    known_locs = [k.lower() for k in prof.known_locations]

                if known_locs:
                    matched = False
                    if curr_city and any(str(curr_city).lower() in k for k in known_locs):
                        matched = True
                    if curr_country and any(str(curr_country).lower() in k for k in known_locs):
                        matched = True

                    if not matched:
                        statuses[SIGNAL_NEW_LOCATION] = SignalStatus.TRUE
                        evidence[SIGNAL_NEW_LOCATION] = {
                            "city": curr_city,
                            "country": curr_country,
                            "known_locations": prof.known_locations,
                        }
                    else:
                        statuses[SIGNAL_NEW_LOCATION] = SignalStatus.FALSE
                else:
                    statuses[SIGNAL_NEW_LOCATION] = SignalStatus.UNKNOWN
            else:
                statuses[SIGNAL_NEW_LOCATION] = SignalStatus.UNKNOWN

        # -------------------------------------------------------------------
        # 3. Unusual Time Signal
        # -------------------------------------------------------------------
        if "unusual_time" in rule_map:
            time_res = rule_map["unusual_time"]
            if time_res.evidence.get("status") == "missing_timestamp" or "Insufficient" in time_res.reason:
                statuses[SIGNAL_UNUSUAL_TIME] = SignalStatus.UNKNOWN
            elif time_res.triggered:
                statuses[SIGNAL_UNUSUAL_TIME] = SignalStatus.TRUE
                evidence[SIGNAL_UNUSUAL_TIME] = time_res.evidence
            else:
                statuses[SIGNAL_UNUSUAL_TIME] = SignalStatus.FALSE
        else:
            statuses[SIGNAL_UNUSUAL_TIME] = SignalStatus.UNKNOWN

        # -------------------------------------------------------------------
        # 4. Failed Login Activity Signal
        # -------------------------------------------------------------------
        failed_threshold = int(context.get_config_value("ATO_FAILED_LOGIN_THRESHOLD", 3))
        if "multiple_failed_login" in rule_map and rule_map["multiple_failed_login"].triggered:
            statuses[SIGNAL_FAILED_LOGIN] = SignalStatus.TRUE
            evidence[SIGNAL_FAILED_LOGIN] = rule_map["multiple_failed_login"].evidence
        else:
            prof = getattr(context, "user_profile", None)
            recent_fails = 0
            if prof and hasattr(prof, "recent_failed_login_count"):
                recent_fails = prof.recent_failed_login_count
            elif context.login_attempts:
                now = datetime.now(timezone.utc)
                window_mins = int(context.get_config_value("ATO_FAILED_LOGIN_WINDOW_MINUTES", 30))
                cutoff = now - timedelta(minutes=window_mins)
                recent_fails = sum(
                    1
                    for la in context.login_attempts
                    if not _safe_get(la, "is_successful", False)
                    and (_safe_get(la, "timestamp") or now) >= cutoff
                )

            if recent_fails >= failed_threshold:
                statuses[SIGNAL_FAILED_LOGIN] = SignalStatus.TRUE
                evidence[SIGNAL_FAILED_LOGIN] = {
                    "recent_failed_attempts": recent_fails,
                    "threshold": failed_threshold,
                }
            elif recent_fails == 0 and (prof or context.login_attempts):
                statuses[SIGNAL_FAILED_LOGIN] = SignalStatus.FALSE
            else:
                statuses[SIGNAL_FAILED_LOGIN] = SignalStatus.UNKNOWN

        # -------------------------------------------------------------------
        # 5. Unusual Transaction Amount Signal
        # -------------------------------------------------------------------
        if "unusual_transaction_amount" in rule_map:
            amt_res = rule_map["unusual_transaction_amount"]
            if "Insufficient" in amt_res.reason:
                statuses[SIGNAL_UNUSUAL_TRANSACTION] = SignalStatus.UNKNOWN
            elif amt_res.triggered:
                statuses[SIGNAL_UNUSUAL_TRANSACTION] = SignalStatus.TRUE
                evidence[SIGNAL_UNUSUAL_TRANSACTION] = amt_res.evidence
            else:
                statuses[SIGNAL_UNUSUAL_TRANSACTION] = SignalStatus.FALSE
        else:
            statuses[SIGNAL_UNUSUAL_TRANSACTION] = SignalStatus.UNKNOWN

        # -------------------------------------------------------------------
        # Tally active signals & determine ATO risk severity
        # -------------------------------------------------------------------
        signals_bool: Dict[str, bool] = {
            k: (v == SignalStatus.TRUE) for k, v in statuses.items()
        }
        active_signals = [k for k, v in signals_bool.items() if v]
        signal_count = len(active_signals)

        med_thresh = int(context.get_config_value("ATO_MEDIUM_SIGNAL_COUNT", 2))
        high_thresh = int(context.get_config_value("ATO_HIGH_SIGNAL_COUNT", 3))
        crit_thresh = int(context.get_config_value("ATO_CRITICAL_SIGNAL_COUNT", 4))

        if signal_count >= crit_thresh:
            risk_level = RiskLevel.CRITICAL
        elif signal_count >= high_thresh:
            risk_level = RiskLevel.HIGH
        elif signal_count >= med_thresh:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        is_at_risk = signal_count >= med_thresh

        # -------------------------------------------------------------------
        # Generate deterministic human-readable explanation
        # -------------------------------------------------------------------
        if signal_count == 0:
            explanation = (
                "No account takeover risk indicators detected. "
                "The transaction conforms to regular account activity patterns."
            )
        elif signal_count == 1:
            name = SIGNAL_LABELS.get(active_signals[0], active_signals[0])
            explanation = (
                f"Low account takeover risk. Only 1 suspicious signal was observed: {name}."
            )
        else:
            names = [SIGNAL_LABELS.get(s, s) for s in active_signals]
            if len(names) == 2:
                names_str = f"{names[0]} and {names[1]}"
            else:
                names_str = ", ".join(names[:-1]) + f", and {names[-1]}"

            explanation = (
                f"Potential account takeover risk is {risk_level.value} because {signal_count} "
                f"suspicious signals were detected: {names_str}."
            )

        triggered_rule_ids = [r.rule_id for r in results if r.triggered]

        logger.info(
            f"ATO Assessment for user={user_id}: risk_level={risk_level.value}, "
            f"signal_count={signal_count}, is_at_risk={is_at_risk}"
        )

        return AccountTakeoverAssessment(
            user_id=user_id,
            transaction_id=transaction_id,
            is_at_risk=is_at_risk,
            risk_level=risk_level,
            signal_count=signal_count,
            signals=signals_bool,
            signal_statuses=statuses,
            triggered_rules=triggered_rule_ids,
            evidence=evidence,
            explanation=explanation,
        )

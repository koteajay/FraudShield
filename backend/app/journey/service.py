"""Transaction Journey Service.

Aggregates historical transactions, authentication attempts, device lifecycle markers,
fraud rule evaluations, and compound risk events into a normalized chronological timeline.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple, Any
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.transaction import Transaction
from app.models.login_attempt import LoginAttempt
from app.models.device import Device
from app.models.fraud_rule_result import FraudRuleResult
from app.models.fraud_flag import FraudFlag
from app.models.enums import RiskLevel, FlagSeverity
from app.journey.schemas import (
    JourneyEvent,
    JourneyEventType,
    JourneySeverity,
    JourneySummary,
    JourneyWindow,
    TransactionJourneyResponse,
)

# Secondary deterministic ordering for events occurring at the exact same timestamp
EVENT_PRIORITY: Dict[str, int] = {
    JourneyEventType.LOGIN_ATTEMPT.value: 1,
    JourneyEventType.DEVICE_EVENT.value: 2,
    JourneyEventType.TRANSACTION.value: 3,
    JourneyEventType.RULE_TRIGGER.value: 4,
    JourneyEventType.RISK_EVENT.value: 5,
}


def _format_location(city: Optional[str], country: Optional[str]) -> Optional[str]:
    """Format city and country into a readable location string."""
    parts = [p.strip() for p in [city, country] if p and p.strip()]
    return ", ".join(parts) if parts else None


def _ensure_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime has tzinfo set to UTC if naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TransactionJourneyService:
    """
    Service responsible for constructing the chronological investigation timeline
    surrounding a subject transaction.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def get_transaction_journey(
        self,
        db: Session,
        transaction_id: str,
        before_minutes: Optional[int] = None,
        after_minutes: Optional[int] = None,
    ) -> Optional[TransactionJourneyResponse]:
        """
        Assemble the chronological transaction journey.

        Raises:
            ValueError: If before_minutes or after_minutes is negative.
        """
        if before_minutes is None:
            before_minutes = self.settings.JOURNEY_BEFORE_MINUTES
        if after_minutes is None:
            after_minutes = self.settings.JOURNEY_AFTER_MINUTES

        if before_minutes < 0 or after_minutes < 0:
            raise ValueError("Time window parameters (before_minutes, after_minutes) cannot be negative.")

        # 1. Fetch target transaction
        target_tx = (
            db.query(Transaction)
            .filter(
                (Transaction.id == transaction_id)
                | (Transaction.transaction_reference == transaction_id)
            )
            .options(
                joinedload(Transaction.rule_results),
                joinedload(Transaction.fraud_flags),
                joinedload(Transaction.device),
            )
            .first()
        )
        if target_tx is None:
            return None

        user_id = target_tx.user_id
        target_timestamp = _ensure_timezone(target_tx.timestamp) or datetime.now(timezone.utc)

        start_time = target_timestamp - timedelta(minutes=before_minutes)
        end_time = target_timestamp + timedelta(minutes=after_minutes)

        return self._assemble_journey_timeline(
            db=db,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            reference_transaction_id=target_tx.id,
        )

    def get_user_journey(
        self,
        db: Session,
        user_id: str,
        before_minutes: Optional[int] = None,
        after_minutes: Optional[int] = None,
    ) -> TransactionJourneyResponse:
        """
        Assemble the chronological journey for a user around their most recent activity.
        """
        if before_minutes is None:
            before_minutes = 60
        if after_minutes is None:
            after_minutes = 0

        if before_minutes < 0 or after_minutes < 0:
            raise ValueError("Time window parameters cannot be negative.")

        latest_tx = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.timestamp.desc())
            .first()
        )

        anchor_time = _ensure_timezone(latest_tx.timestamp) if latest_tx else datetime.now(timezone.utc)
        start_time = anchor_time - timedelta(minutes=before_minutes)
        end_time = anchor_time + timedelta(minutes=after_minutes)

        target_tx_id = latest_tx.id if latest_tx else f"user-{user_id}"

        return self._assemble_journey_timeline(
            db=db,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            reference_transaction_id=target_tx_id,
        )

    def _assemble_journey_timeline(
        self,
        db: Session,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        reference_transaction_id: str,
    ) -> TransactionJourneyResponse:
        """Internal timeline builder shared between transaction-level and user-level journey queries."""
        # 2. Query all transactions for user within the time window
        transactions: List[Transaction] = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.timestamp >= start_time,
                Transaction.timestamp <= end_time,
            )
            .options(
                joinedload(Transaction.rule_results),
                joinedload(Transaction.fraud_flags),
                joinedload(Transaction.device),
            )
            .order_by(Transaction.timestamp.asc())
            .all()
        )

        # 3. Query all login attempts for user within the time window
        login_attempts: List[LoginAttempt] = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.user_id == user_id,
                LoginAttempt.timestamp >= start_time,
                LoginAttempt.timestamp <= end_time,
            )
            .order_by(LoginAttempt.timestamp.asc())
            .all()
        )

        # 4. Query all devices enrolled for user to evaluate device events and new device status
        user_devices: List[Device] = (
            db.query(Device)
            .filter(Device.user_id == user_id)
            .order_by(Device.first_seen_at.asc())
            .all()
        )

        events: List[JourneyEvent] = []
        locations_seen: List[str] = []
        devices_seen: List[str] = []
        new_device_detected = False

        def _track_location(loc: Optional[str]) -> None:
            if loc and loc not in locations_seen:
                locations_seen.append(loc)

        def _track_device(dev_id: Optional[str]) -> None:
            if dev_id and dev_id not in devices_seen:
                devices_seen.append(dev_id)

        # Build Device Events (New device first seen within journey window)
        for dev in user_devices:
            dev_first_seen = _ensure_timezone(dev.first_seen_at)
            if dev_first_seen and start_time <= dev_first_seen <= end_time:
                new_device_detected = True
                _track_device(dev.device_id)
                events.append(
                    JourneyEvent(
                        event_id=f"dev-{dev.id}-firstseen",
                        event_type=JourneyEventType.DEVICE_EVENT.value,
                        timestamp=dev_first_seen,
                        transaction_id=None,
                        user_id=user_id,
                        title="New Device Encountered",
                        description=(
                            f"Unrecognized device '{dev.device_id}' "
                            f"({dev.browser or 'Unknown Browser'}, {dev.operating_system or 'Unknown OS'}) "
                            f"was first recorded for this user."
                        ),
                        location=None,
                        device_id=dev.device_id,
                        severity=JourneySeverity.MEDIUM.value,
                        metadata={
                            "browser": dev.browser,
                            "operating_system": dev.operating_system,
                            "ip_address": dev.ip_address,
                            "is_new_device": True,
                        },
                    )
                )

        # Build Login Attempt Events
        for login in login_attempts:
            login_time = _ensure_timezone(login.timestamp)
            login_loc = _format_location(login.city, login.country) or login.ip_address
            _track_location(login_loc)
            _track_device(login.device_id)

            if login.is_successful:
                sev = JourneySeverity.INFO.value
                title = "Successful Login"
                desc = "User authentication succeeded."
            else:
                sev = JourneySeverity.HIGH.value if login.is_suspicious else JourneySeverity.MEDIUM.value
                reason = f": {login.failure_reason}" if login.failure_reason else ""
                title = "Failed Login Attempt"
                desc = f"User authentication failed{reason}."

            events.append(
                JourneyEvent(
                    event_id=f"login-{login.id}",
                    event_type=JourneyEventType.LOGIN_ATTEMPT.value,
                    timestamp=login_time,
                    transaction_id=None,
                    user_id=user_id,
                    title=title,
                    description=desc,
                    location=login_loc,
                    device_id=login.device_id,
                    risk_score=login.risk_score,
                    severity=sev,
                    metadata={
                        "is_successful": login.is_successful,
                        "failure_reason": login.failure_reason,
                        "ip_address": login.ip_address,
                        "user_agent": login.user_agent,
                        "is_suspicious": login.is_suspicious,
                    },
                )
            )

        # Build Transaction, Rule Trigger, and Risk Events
        for tx in transactions:
            tx_time = _ensure_timezone(tx.timestamp)
            tx_loc = _format_location(tx.city, tx.country)
            dev_id = tx.device.device_id if tx.device else tx.device_id
            _track_location(tx_loc)
            _track_device(dev_id)

            risk_level_str = (
                tx.risk_level.value if hasattr(tx.risk_level, "value") else str(tx.risk_level)
            )

            # Determine transaction title & severity
            if tx.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                tx_title = f"{risk_level_str.capitalize()} Risk Transaction"
                tx_sev = (
                    JourneySeverity.CRITICAL.value
                    if tx.risk_level == RiskLevel.CRITICAL
                    else JourneySeverity.HIGH.value
                )
            elif tx.risk_level == RiskLevel.MEDIUM:
                tx_title = "Medium Risk Transaction"
                tx_sev = JourneySeverity.MEDIUM.value
            else:
                tx_title = "Transaction"
                tx_sev = JourneySeverity.INFO.value

            desc = f"{tx.currency} {tx.amount:,.2f} transaction"
            if tx.merchant_name:
                desc += f" at {tx.merchant_name}"

            # 1. Exactly ONE Transaction Event per Transaction
            events.append(
                JourneyEvent(
                    event_id=f"txn-{tx.id}",
                    event_type=JourneyEventType.TRANSACTION.value,
                    timestamp=tx_time,
                    transaction_id=tx.id,
                    user_id=user_id,
                    title=tx_title,
                    description=desc,
                    location=tx_loc,
                    device_id=dev_id,
                    amount=tx.amount,
                    currency=tx.currency,
                    risk_score=tx.risk_score,
                    risk_level=risk_level_str,
                    severity=tx_sev,
                    metadata={
                        "reference": tx.transaction_reference,
                        "status": tx.status.value if hasattr(tx.status, "value") else str(tx.status),
                        "merchant_name": tx.merchant_name,
                        "merchant_category": tx.merchant_category,
                        "payment_method": tx.payment_method,
                        "is_target_transaction": (tx.id == reference_transaction_id),
                    },
                )
            )

            # 2. Separate Rule Trigger Events for Each Triggered Rule
            for rule in (tx.rule_results or []):
                if rule.is_triggered:
                    rule_sev = (
                        rule.severity.value
                        if hasattr(rule.severity, "value")
                        else str(rule.severity or "MEDIUM")
                    )

                    reason = ""
                    evidence = {}
                    contrib = rule.weight

                    if isinstance(rule.details, dict):
                        reason = rule.details.get("reason", "")
                        evidence = rule.details.get("evidence", rule.details)
                        contrib = rule.details.get("score_contribution", rule.weight)

                    if not reason:
                        reason = f"Rule '{rule.rule_name}' condition was triggered."

                    if rule.rule_id == "device_change":
                        new_device_detected = True

                    events.append(
                        JourneyEvent(
                            event_id=f"rule-{rule.id}",
                            event_type=JourneyEventType.RULE_TRIGGER.value,
                            timestamp=tx_time,
                            transaction_id=tx.id,
                            user_id=user_id,
                            title=rule.rule_name,
                            description=reason,
                            location=tx_loc,
                            device_id=dev_id,
                            rule_id=rule.rule_id,
                            severity=rule_sev,
                            metadata={
                                "rule_name": rule.rule_name,
                                "rule_category": rule.rule_category,
                                "score_contribution": contrib,
                                "evidence": evidence,
                                "reason": reason,
                            },
                        )
                    )

            # 3. Risk Events (Fraud Flags or Elevated Risk Scores)
            if tx.fraud_flags:
                for flag in tx.fraud_flags:
                    flag_sev = (
                        flag.severity.value
                        if hasattr(flag.severity, "value")
                        else str(flag.severity)
                    )
                    flag_time = _ensure_timezone(flag.created_at) or tx_time
                    events.append(
                        JourneyEvent(
                            event_id=f"flag-{flag.id}",
                            event_type=JourneyEventType.RISK_EVENT.value,
                            timestamp=flag_time,
                            transaction_id=tx.id,
                            user_id=user_id,
                            title=f"Fraud Flag: {flag.flag_type.replace('_', ' ').title()}",
                            description=flag.reason,
                            location=tx_loc,
                            device_id=dev_id,
                            risk_score=tx.risk_score,
                            risk_level=risk_level_str,
                            severity=flag_sev,
                            metadata={"flag_type": flag.flag_type},
                        )
                    )
            elif tx.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                events.append(
                    JourneyEvent(
                        event_id=f"risk-tx-{tx.id}",
                        event_type=JourneyEventType.RISK_EVENT.value,
                        timestamp=tx_time,
                        transaction_id=tx.id,
                        user_id=user_id,
                        title=f"Elevated Risk: {risk_level_str.capitalize()}",
                        description=(
                            f"Transaction evaluated with risk score {tx.risk_score:.0f}/100 "
                            f"resulting in a {risk_level_str} risk classification."
                        ),
                        location=tx_loc,
                        device_id=dev_id,
                        risk_score=tx.risk_score,
                        risk_level=risk_level_str,
                        severity=(
                            JourneySeverity.CRITICAL.value
                            if tx.risk_level == RiskLevel.CRITICAL
                            else JourneySeverity.HIGH.value
                        ),
                        metadata={"score": tx.risk_score, "level": risk_level_str},
                    )
                )

        # 5. Sort Events Chronologically with Deterministic Tie-Breaker
        events.sort(
            key=lambda e: (
                e.timestamp,
                EVENT_PRIORITY.get(e.event_type, 99),
                e.event_id,
            )
        )

        # 6. Aggregate Summary
        tx_count = sum(1 for e in events if e.event_type == JourneyEventType.TRANSACTION.value)
        login_count = sum(1 for e in events if e.event_type == JourneyEventType.LOGIN_ATTEMPT.value)
        rule_count = sum(1 for e in events if e.event_type == JourneyEventType.RULE_TRIGGER.value)
        risk_count = sum(1 for e in events if e.event_type == JourneyEventType.RISK_EVENT.value)

        summary = JourneySummary(
            transaction_count=tx_count,
            login_attempt_count=login_count,
            rule_trigger_count=rule_count,
            risk_event_count=risk_count,
            new_device_detected=new_device_detected,
            locations=locations_seen,
            devices=devices_seen,
        )

        return TransactionJourneyResponse(
            transaction_id=reference_transaction_id,
            user_id=user_id,
            window=JourneyWindow(start=start_time, end=end_time),
            events=events,
            summary=summary,
        )


"""Phase 8 Transaction Journey Test Suite.

Validates chronological event assembly, normalized representations, time window filtering,
duplicate protection, missing data resilience, suspicious multi-event scenarios, and API endpoints.
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db, init_db, SessionLocal
from app.main import app
from app.models.device import Device
from app.models.enums import FlagSeverity, RiskLevel, TransactionStatus
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.login_attempt import LoginAttempt
from app.models.transaction import Transaction
from app.models.user import User
from app.journey.schemas import JourneyEventType, JourneySeverity
from app.journey.service import TransactionJourneyService


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema is ready before each test."""
    init_db()


@pytest.fixture
def db_session():
    """Yield a transactional database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client():
    """Yield a FastAPI TestClient."""
    return TestClient(app)


def _create_user(db: Session, user_id: str, email: str = "test@example.com") -> User:
    """Helper to create a user."""
    user = User(
        id=user_id,
        email=f"{user_id}_{email}",
        username=f"user_{user_id}",
        full_name="Journey Test User",
        phone_number="+919876543210",
    )
    db.merge(user)
    db.commit()
    return user


def _create_device(
    db: Session,
    user_id: str,
    device_id: str,
    first_seen_at: datetime,
    browser: str = "Chrome",
    os: str = "Windows",
) -> Device:
    """Helper to create a client device."""
    dev = Device(
        id=str(uuid.uuid4()),
        user_id=user_id,
        device_id=device_id,
        browser=browser,
        operating_system=os,
        first_seen_at=first_seen_at,
        last_seen_at=first_seen_at,
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return dev


# ---------------------------------------------------------------------------
# 1. BASIC JOURNEY & CHRONOLOGICAL ORDERING
# ---------------------------------------------------------------------------

def test_basic_journey_includes_target_transaction_and_chronology(db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    base_time = datetime(2026, 9, 30, 10, 20, tzinfo=timezone.utc)

    # Earlier transaction (10:02)
    tx1 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-1-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=2000.0,
        currency="INR",
        city="Hyderabad",
        country="IN",
        timestamp=base_time - timedelta(minutes=18),
        risk_score=10.0,
        risk_level=RiskLevel.LOW,
    )
    # Target transaction (10:20)
    tx2 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-2-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=75000.0,
        currency="INR",
        city="Delhi",
        country="IN",
        timestamp=base_time,
        risk_score=85.0,
        risk_level=RiskLevel.CRITICAL,
    )
    # Later transaction (10:35)
    tx3 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-3-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=500.0,
        currency="INR",
        city="Delhi",
        country="IN",
        timestamp=base_time + timedelta(minutes=15),
        risk_score=15.0,
        risk_level=RiskLevel.LOW,
    )

    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(db_session, transaction_id=tx2.id, before_minutes=30, after_minutes=30)

    assert journey is not None
    assert journey.transaction_id == tx2.id
    assert journey.user_id == user_id
    assert len(journey.events) >= 3

    # Check timestamps are strictly chronological
    for i in range(len(journey.events) - 1):
        assert journey.events[i].timestamp <= journey.events[i + 1].timestamp

    # Verify target transaction is present
    tx_events = [e for e in journey.events if e.event_type == JourneyEventType.TRANSACTION.value]
    target_events = [e for e in tx_events if e.transaction_id == tx2.id]
    assert len(target_events) == 1
    assert target_events[0].amount == 75000.0
    assert target_events[0].metadata["is_target_transaction"] is True


# ---------------------------------------------------------------------------
# 2. EVENT TYPES REPERTOIRE
# ---------------------------------------------------------------------------

def test_journey_event_types_repertoire(db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    base_time = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)

    # 1. Device registration (11:45) -> DEVICE_EVENT
    dev = _create_device(
        db_session,
        user_id=user_id,
        device_id="DEV-LAPTOP-1",
        first_seen_at=base_time - timedelta(minutes=15),
    )

    # 2. Login attempt (11:50) -> LOGIN_ATTEMPT
    login = LoginAttempt(
        id=str(uuid.uuid4()),
        user_id=user_id,
        attempted_email="user@test.com",
        device_id=dev.device_id,
        city="Mumbai",
        country="IN",
        is_successful=False,
        failure_reason="INVALID_PASSWORD",
        is_suspicious=True,
        timestamp=base_time - timedelta(minutes=10),
    )
    db_session.add(login)

    # 3. Transaction with rule results and fraud flags (12:00) -> TRANSACTION, RULE_TRIGGER, RISK_EVENT
    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-REP-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=50000.0,
        currency="INR",
        city="Mumbai",
        country="IN",
        device_id=dev.id,
        timestamp=base_time,
        risk_score=75.0,
        risk_level=RiskLevel.HIGH,
    )
    db_session.add(tx)
    db_session.flush()

    # Add triggered rule result
    rule_res = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        rule_id="unusual_transaction_amount",
        rule_name="Unusual Transaction Amount",
        rule_category="BEHAVIORAL",
        is_triggered=True,
        weight=1.0,
        severity=FlagSeverity.HIGH,
        details={"reason": "Amount spike detected", "score_contribution": 30.0},
    )
    # Add fraud flag
    flag = FraudFlag(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        flag_type="AMOUNT_ANOMALY",
        severity=FlagSeverity.HIGH,
        reason="Transaction spike 5x baseline",
        created_at=base_time,
    )
    db_session.add_all([rule_res, flag])
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(db_session, transaction_id=tx.id, before_minutes=30, after_minutes=30)

    assert journey is not None
    event_types = {e.event_type for e in journey.events}

    assert JourneyEventType.TRANSACTION.value in event_types
    assert JourneyEventType.LOGIN_ATTEMPT.value in event_types
    assert JourneyEventType.DEVICE_EVENT.value in event_types
    assert JourneyEventType.RULE_TRIGGER.value in event_types
    assert JourneyEventType.RISK_EVENT.value in event_types

    assert journey.summary.transaction_count >= 1
    assert journey.summary.login_attempt_count >= 1
    assert journey.summary.rule_trigger_count >= 1
    assert journey.summary.risk_event_count >= 1
    assert journey.summary.new_device_detected is True


# ---------------------------------------------------------------------------
# 3. TIME WINDOW BOUNDARY FILTERING
# ---------------------------------------------------------------------------

def test_journey_time_window_filtering(db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    target_time = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)

    # 1 hour before -> OUTSIDE (before_minutes=30)
    tx_way_before = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-BEFORE-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=100.0,
        timestamp=target_time - timedelta(minutes=60),
    )
    # 20 minutes before -> INSIDE
    tx_inside_before = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-INSIDE-1-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=200.0,
        timestamp=target_time - timedelta(minutes=20),
    )
    # Target transaction (15:00) -> INSIDE
    tx_target = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-TARGET-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=300.0,
        timestamp=target_time,
    )
    # 25 minutes after -> INSIDE (after_minutes=30)
    tx_inside_after = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-INSIDE-2-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=400.0,
        timestamp=target_time + timedelta(minutes=25),
    )
    # 45 minutes after -> OUTSIDE
    tx_way_after = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-AFTER-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=500.0,
        timestamp=target_time + timedelta(minutes=45),
    )

    db_session.add_all([tx_way_before, tx_inside_before, tx_target, tx_inside_after, tx_way_after])
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(
        db_session,
        transaction_id=tx_target.id,
        before_minutes=30,
        after_minutes=30,
    )

    assert journey is not None
    tx_ids_in_journey = {
        e.transaction_id for e in journey.events if e.event_type == JourneyEventType.TRANSACTION.value
    }

    assert tx_target.id in tx_ids_in_journey
    assert tx_inside_before.id in tx_ids_in_journey
    assert tx_inside_after.id in tx_ids_in_journey
    assert tx_way_before.id not in tx_ids_in_journey
    assert tx_way_after.id not in tx_ids_in_journey


# ---------------------------------------------------------------------------
# 4. DUPLICATE PROTECTION (TRANSACTION WITH MULTIPLE RULES)
# ---------------------------------------------------------------------------

def test_duplicate_protection_with_multiple_rules(db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    target_time = datetime(2026, 9, 30, 16, 0, tzinfo=timezone.utc)

    # Transaction with 3 triggered rules
    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-DUP-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=75000.0,
        currency="INR",
        city="Delhi",
        country="IN",
        timestamp=target_time,
        risk_score=82.0,
        risk_level=RiskLevel.CRITICAL,
    )
    db_session.add(tx)
    db_session.flush()

    rule1 = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        rule_id="unusual_amount",
        rule_name="Unusual Amount",
        is_triggered=True,
        weight=1.0,
        details={"reason": "Amount spike"},
    )
    rule2 = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        rule_id="device_change",
        rule_name="Device Change",
        is_triggered=True,
        weight=1.0,
        details={"reason": "New device observed"},
    )
    rule3 = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        rule_id="unusual_time",
        rule_name="Unusual Time",
        is_triggered=True,
        weight=1.0,
        details={"reason": "Night activity"},
    )
    db_session.add_all([rule1, rule2, rule3])
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(db_session, transaction_id=tx.id)

    assert journey is not None

    # TRANSACTION event must appear EXACTLY ONCE
    tx_events = [e for e in journey.events if e.event_type == JourneyEventType.TRANSACTION.value]
    assert len(tx_events) == 1
    assert tx_events[0].transaction_id == tx.id

    # RULE_TRIGGER events must appear separately for each rule
    rule_events = [e for e in journey.events if e.event_type == JourneyEventType.RULE_TRIGGER.value]
    assert len(rule_events) == 3
    rule_ids = {r.rule_id for r in rule_events}
    assert rule_ids == {"unusual_amount", "device_change", "unusual_time"}


# ---------------------------------------------------------------------------
# 5. MISSING DATA RESILIENCE (COLD START / BARE TRANSACTION)
# ---------------------------------------------------------------------------

def test_missing_data_resilience(db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    # Bare transaction with no devices, no login attempts, no rule results, no flags
    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-BARE-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=100.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        risk_score=0.0,
        risk_level=RiskLevel.LOW,
    )
    db_session.add(tx)
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(db_session, transaction_id=tx.id)

    assert journey is not None
    assert journey.transaction_id == tx.id
    assert journey.summary.transaction_count == 1
    assert journey.summary.login_attempt_count == 0
    assert journey.summary.rule_trigger_count == 0
    assert journey.summary.risk_event_count == 0
    assert journey.summary.new_device_detected is False
    assert len(journey.events) == 1
    assert journey.events[0].event_type == JourneyEventType.TRANSACTION.value


# ---------------------------------------------------------------------------
# 6. REALISTIC SUSPICIOUS ACCOUNT TAKEOVER SCENARIO
# ---------------------------------------------------------------------------

def test_suspicious_scenario_journey_storyline(db_session: Session):
    """
    Scenario from Goal:
    10:02 -> Hyderabad -> ₹2,000 -> Device A
    10:15 -> Hyderabad -> ₹3,500 -> Device A
    10:21 -> Delhi     -> ₹75,000 -> Device X (High-risk transaction, multiple rules)
    10:23 -> Delhi     -> Failed Login -> Device X
    """
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    t_09_00 = datetime(2026, 9, 30, 9, 0, tzinfo=timezone.utc)
    dev_a = _create_device(db_session, user_id, "Device-A", first_seen_at=t_09_00)

    t_10_02 = datetime(2026, 9, 30, 10, 2, tzinfo=timezone.utc)
    t_10_15 = datetime(2026, 9, 30, 10, 15, tzinfo=timezone.utc)
    t_10_20 = datetime(2026, 9, 30, 10, 20, tzinfo=timezone.utc)  # Device X first seen
    t_10_21 = datetime(2026, 9, 30, 10, 21, tzinfo=timezone.utc)  # Large suspicious txn
    t_10_23 = datetime(2026, 9, 30, 10, 23, tzinfo=timezone.utc)  # Failed login

    # Device X registered at 10:20 (inside window)
    dev_x = _create_device(db_session, user_id, "Device-X", first_seen_at=t_10_20)

    # 10:02 Transaction (Device A, Hyderabad)
    tx1 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-NORM1-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=2000.0,
        currency="INR",
        city="Hyderabad",
        country="IN",
        device_id=dev_a.id,
        timestamp=t_10_02,
        risk_score=5.0,
        risk_level=RiskLevel.LOW,
    )

    # 10:15 Transaction (Device A, Hyderabad)
    tx2 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-NORM2-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=3500.0,
        currency="INR",
        city="Hyderabad",
        country="IN",
        device_id=dev_a.id,
        timestamp=t_10_15,
        risk_score=5.0,
        risk_level=RiskLevel.LOW,
    )

    # 10:21 Suspicious Transaction (Device X, Delhi)
    tx3 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-SUSP-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=75000.0,
        currency="INR",
        city="Delhi",
        country="IN",
        device_id=dev_x.id,
        timestamp=t_10_21,
        risk_score=82.0,
        risk_level=RiskLevel.CRITICAL,
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.flush()

    # Rule triggers for tx3
    r_amt = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx3.id,
        rule_id="unusual_amount",
        rule_name="Unusual Transaction Amount",
        is_triggered=True,
        weight=1.0,
        details={"reason": "Amount spike ₹75,000", "score_contribution": 30.0},
    )
    r_dev = FraudRuleResult(
        id=str(uuid.uuid4()),
        transaction_id=tx3.id,
        rule_id="device_change",
        rule_name="Device Change",
        is_triggered=True,
        weight=1.0,
        details={"reason": "Unrecognized Device X", "score_contribution": 15.0},
    )
    db_session.add_all([r_amt, r_dev])

    # 10:23 Failed Login (Device X, Delhi)
    login_fail = LoginAttempt(
        id=str(uuid.uuid4()),
        user_id=user_id,
        attempted_email="user@test.com",
        device_id="Device-X",
        city="Delhi",
        country="IN",
        is_successful=False,
        failure_reason="INVALID_PASSWORD",
        is_suspicious=True,
        timestamp=t_10_23,
    )
    db_session.add(login_fail)
    db_session.commit()

    service = TransactionJourneyService()
    journey = service.get_transaction_journey(db_session, transaction_id=tx3.id, before_minutes=30, after_minutes=30)

    assert journey is not None
    assert journey.summary.new_device_detected is True
    assert "Hyderabad, IN" in journey.summary.locations
    assert "Delhi, IN" in journey.summary.locations
    assert "Device-A" in journey.summary.devices
    assert "Device-X" in journey.summary.devices

    # Verify chronological order
    for i in range(len(journey.events) - 1):
        assert journey.events[i].timestamp <= journey.events[i + 1].timestamp

    # Check that failed login is at the end
    last_event = journey.events[-1]
    assert last_event.event_type == JourneyEventType.LOGIN_ATTEMPT.value
    assert last_event.location == "Delhi, IN"
    assert last_event.metadata["is_successful"] is False


# ---------------------------------------------------------------------------
# 7. REST API ENDPOINT TESTS (GET /api/transactions/{id}/journey)
# ---------------------------------------------------------------------------

def test_api_journey_success(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-API-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=1500.0,
        currency="USD",
        timestamp=datetime.now(timezone.utc),
        risk_score=12.0,
        risk_level=RiskLevel.LOW,
    )
    db_session.add(tx)
    db_session.commit()

    response = test_client.get(f"/api/transactions/{tx.id}/journey?before_minutes=15&after_minutes=15")
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == tx.id
    assert data["user_id"] == user_id
    assert "window" in data
    assert "events" in data
    assert "summary" in data
    assert data["summary"]["transaction_count"] == 1


def test_api_journey_not_found(test_client: TestClient):
    response = test_client.get("/api/transactions/nonexistent-txn-id/journey")
    assert response.status_code == 404
    err = response.json()
    assert "error" in err or "detail" in err


def test_api_journey_negative_window_rejected(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _create_user(db_session, user_id)

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-NEG-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=100.0,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx)
    db_session.commit()

    # Negative before_minutes
    resp1 = test_client.get(f"/api/transactions/{tx.id}/journey?before_minutes=-10")
    assert resp1.status_code == 400

    # Negative after_minutes
    resp2 = test_client.get(f"/api/transactions/{tx.id}/journey?after_minutes=-5")
    assert resp2.status_code == 400

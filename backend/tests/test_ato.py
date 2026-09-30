"""Comprehensive Unit and Integration Tests for Phase 7 Unusual Time & Account Takeover (ATO) Detection."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, RiskLevel, TransactionStatus
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.login_attempt import LoginAttempt

from app.fraud.context import RuleContext
from app.fraud.result import RuleResult
from app.fraud.rules.unusual_time import UnusualTimeRule
from app.fraud.rules.device_change import DeviceChangeRule
from app.fraud.rules.unusual_amount import UnusualTransactionAmountRule
from app.fraud.rules.failed_login import MultipleFailedLoginRule
from app.fraud.rules.impossible_location import ImpossibleGeographicalLocationRule

from app.behaviour.models import UserBehaviourProfile, ProfileStatus
from app.security.models import AccountTakeoverAssessment, SignalStatus
from app.security.account_takeover import (
    AccountTakeoverDetector,
    SIGNAL_NEW_DEVICE,
    SIGNAL_NEW_LOCATION,
    SIGNAL_UNUSUAL_TIME,
    SIGNAL_FAILED_LOGIN,
    SIGNAL_UNUSUAL_TRANSACTION,
)


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides isolated in-memory SQLite database session."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(name="client")
def fixture_client(db_session: Session):
    """FastAPI test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. UNUSUAL TIME RULE: UNIT & PROPERTY TESTS
# ---------------------------------------------------------------------------

def test_unusual_time_normal_hours():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 14, 30, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False
    assert res.score_contribution == 0.0
    assert res.evidence["outside_normal_hours"] is False
    assert "consistent with the user's active time window" in res.reason


def test_unusual_time_outside_normal_hours():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 3, 15, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is True
    assert res.score_contribution == 10.0
    assert res.evidence["transaction_time"] == "03:15"
    assert res.evidence["normal_start"] == "08:00"
    assert res.evidence["normal_end"] == "22:00"
    assert res.evidence["outside_normal_hours"] is True
    assert "outside the user's regular activity hours" in res.reason


def test_unusual_time_exact_start_boundary():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        profile_transaction_count=20,
    )
    # Exactly 08:00
    ctx = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False


def test_unusual_time_exact_end_boundary():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        profile_transaction_count=20,
    )
    # Exactly 22:00
    ctx = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 22, 0, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False


def test_unusual_time_overnight_window():
    rule = UnusualTimeRule()
    # Normal activity crosses midnight: 22:00 (10 PM) to 04:00 (4 AM)
    profile = UserBehaviourProfile(
        user_id="U_NIGHT",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=22,
        normal_transaction_end_hour=4,
        profile_transaction_count=25,
    )

    # 1. 23:30 -> inside overnight window
    ctx1 = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res1 = rule.evaluate(ctx1)
    assert res1.triggered is False

    # 2. 02:15 -> inside overnight window
    ctx2 = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 2, 2, 15, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res2 = rule.evaluate(ctx2)
    assert res2.triggered is False

    # 3. 12:00 -> outside overnight window
    ctx3 = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res3 = rule.evaluate(ctx3)
    assert res3.triggered is True
    assert res3.evidence["outside_normal_hours"] is True


def test_unusual_time_insufficient_history():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U_NEW",
        profile_status=ProfileStatus.INSUFFICIENT_DATA,
        normal_transaction_start_hour=None,
        normal_transaction_end_hour=None,
        profile_transaction_count=2,
    )
    ctx = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 3, 15, tzinfo=timezone.utc)},
        user_profile=profile,
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False
    assert res.score_contribution == 0.0
    assert "Insufficient historical data" in res.reason


def test_unusual_time_missing_timestamp():
    rule = UnusualTimeRule()
    # Transaction dictionary omitting timestamp
    ctx = RuleContext(
        current_transaction={"id": "tx_no_ts", "amount": 100.0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False
    assert res.evidence.get("status") == "missing_timestamp"
    assert "does not contain a timestamp" in res.reason


def test_unusual_time_timezone_conversion():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=9,
        normal_transaction_end_hour=18,
        profile_transaction_count=20,
    )

    # 04:30 UTC is 10:00 AM in Asia/Kolkata (+05:30)
    utc_ts = datetime(2026, 1, 1, 4, 30, tzinfo=timezone.utc)
    ctx = RuleContext(
        current_transaction={"timestamp": utc_ts, "timezone": "Asia/Kolkata"},
        user_profile=profile,
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    res = rule.evaluate(ctx)
    assert res.triggered is False  # In Asia/Kolkata it is 10:00 (inside 9–18)
    assert res.evidence["current_hour"] == 10
    assert res.evidence["transaction_time"] == "10:00"


# ---------------------------------------------------------------------------
# 2. ATO DETECTOR: THRESHOLD & SIGNAL COUNT TESTS
# ---------------------------------------------------------------------------

def test_ato_zero_signals():
    detector = AccountTakeoverDetector()
    ctx = RuleContext(current_transaction={"user_id": "U1"})
    # All rules passed and not triggered
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=False, reason="Device is recognized", score_contribution=0.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=False, reason="Normal time", score_contribution=0.0),
        RuleResult(rule_id="multiple_failed_login", rule_name="Failed Login", triggered=False, reason="No failed logins", score_contribution=0.0),
        RuleResult(rule_id="unusual_transaction_amount", rule_name="Unusual Amount", triggered=False, reason="Normal amount", score_contribution=0.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 0
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.is_at_risk is False
    assert "No account takeover risk indicators detected" in assessment.explanation


def test_ato_one_signal():
    detector = AccountTakeoverDetector()
    ctx = RuleContext(current_transaction={"user_id": "U1"})
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=True, reason="New device", score_contribution=15.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=False, reason="Normal time", score_contribution=0.0),
        RuleResult(rule_id="multiple_failed_login", rule_name="Failed Login", triggered=False, reason="No failed logins", score_contribution=0.0),
        RuleResult(rule_id="unusual_transaction_amount", rule_name="Unusual Amount", triggered=False, reason="Normal amount", score_contribution=0.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 1
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.is_at_risk is False
    assert assessment.signals[SIGNAL_NEW_DEVICE] is True
    assert "Low account takeover risk" in assessment.explanation


def test_ato_two_signals_medium():
    detector = AccountTakeoverDetector()
    ctx = RuleContext(current_transaction={"user_id": "U1"})
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=True, reason="New device", score_contribution=15.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=True, reason="Unusual time", score_contribution=10.0),
        RuleResult(rule_id="multiple_failed_login", rule_name="Failed Login", triggered=False, reason="No failed logins", score_contribution=0.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 2
    assert assessment.risk_level == RiskLevel.MEDIUM
    assert assessment.is_at_risk is True
    assert "Potential account takeover risk is MEDIUM" in assessment.explanation


def test_ato_three_signals_high():
    detector = AccountTakeoverDetector()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_locations=["Hyderabad, IN"],
        profile_transaction_count=20,
    )
    # New device + Unusual time + New Location (from unknown city)
    ctx = RuleContext(
        current_transaction={"user_id": "U1", "city": "London", "country": "UK"},
        user_profile=profile,
    )
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=True, reason="New device", score_contribution=15.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=True, reason="Unusual time", score_contribution=10.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 3
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.is_at_risk is True
    assert assessment.signals[SIGNAL_NEW_LOCATION] is True
    assert "Potential account takeover risk is HIGH" in assessment.explanation


def test_ato_four_signals_critical():
    detector = AccountTakeoverDetector()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_locations=["Hyderabad, IN"],
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={"user_id": "U1", "city": "Dubai", "country": "UAE"},
        user_profile=profile,
    )
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=True, reason="New device", score_contribution=15.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=True, reason="Unusual time", score_contribution=10.0),
        RuleResult(rule_id="multiple_failed_login", rule_name="Failed Login", triggered=True, reason="Multiple failed logins", score_contribution=20.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 4
    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.is_at_risk is True
    assert "Potential account takeover risk is CRITICAL" in assessment.explanation


def test_ato_five_signals_critical():
    detector = AccountTakeoverDetector()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_locations=["Hyderabad, IN"],
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={"user_id": "U1", "city": "Moscow", "country": "RU"},
        user_profile=profile,
    )
    results = [
        RuleResult(rule_id="device_change", rule_name="Device Change", triggered=True, reason="New device", score_contribution=15.0),
        RuleResult(rule_id="unusual_time", rule_name="Unusual Time", triggered=True, reason="Unusual time", score_contribution=10.0),
        RuleResult(rule_id="multiple_failed_login", rule_name="Failed Login", triggered=True, reason="Multiple failed logins", score_contribution=20.0),
        RuleResult(rule_id="unusual_transaction_amount", rule_name="Unusual Amount", triggered=True, reason="High amount", score_contribution=30.0),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_count == 5
    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.is_at_risk is True
    assert all(assessment.signals.values())


# ---------------------------------------------------------------------------
# 3. TRI-STATE UNKNOWN VS FALSE HANDLING
# ---------------------------------------------------------------------------

def test_ato_unknown_signals_handling():
    detector = AccountTakeoverDetector()
    # Transaction without device, location, or login history
    ctx = RuleContext(current_transaction={"user_id": "U_BARE"})
    results = [
        RuleResult(
            rule_id="device_change",
            rule_name="Device Change",
            triggered=False,
            reason="Missing device telemetry",
            evidence={"status": "missing_device_telemetry"},
        ),
        RuleResult(
            rule_id="unusual_time",
            rule_name="Unusual Time",
            triggered=False,
            reason="Transaction does not contain a timestamp.",
            evidence={"status": "missing_timestamp"},
        ),
    ]
    assessment = detector.evaluate(ctx, results)
    assert assessment.signal_statuses[SIGNAL_NEW_DEVICE] == SignalStatus.UNKNOWN
    assert assessment.signal_statuses[SIGNAL_UNUSUAL_TIME] == SignalStatus.UNKNOWN
    assert assessment.signal_statuses[SIGNAL_NEW_LOCATION] == SignalStatus.UNKNOWN
    # UNKNOWN signals must NOT increment signal_count
    assert assessment.signal_count == 0
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.is_at_risk is False


# ---------------------------------------------------------------------------
# 4. REALISTIC ATO INTEGRATION SCENARIOS
# ---------------------------------------------------------------------------

def test_ato_scenario_1_normal_transaction():
    """Scenario 1: Known device, known location, normal time, no failed logins, normal amount."""
    profile = UserBehaviourProfile(
        user_id="U_NORM",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["TRUSTED-DEV-1"],
        known_locations=["Hyderabad, IN"],
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        average_transaction_amount=3000.0,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={
            "user_id": "U_NORM",
            "device_id": "TRUSTED-DEV-1",
            "city": "Hyderabad",
            "country": "IN",
            "amount": 2500.0,
            "timestamp": datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc),
        },
        user_profile=profile,
        known_devices=[Device(id="dev1", device_id="TRUSTED-DEV-1")],
    )
    # Evaluate rules
    dev_res = DeviceChangeRule().evaluate(ctx)
    time_res = UnusualTimeRule().evaluate(ctx)
    amt_res = UnusualTransactionAmountRule().evaluate(ctx)

    assessment = AccountTakeoverDetector().evaluate(ctx, [dev_res, time_res, amt_res])
    assert assessment.is_at_risk is False
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.signal_count == 0


def test_ato_scenario_2_new_device_only():
    """Scenario 2: New device only -> Low ATO risk."""
    profile = UserBehaviourProfile(
        user_id="U_SCEN2",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["OLD-DEV-1"],
        known_locations=["Hyderabad, IN"],
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        average_transaction_amount=3000.0,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={
            "user_id": "U_SCEN2",
            "device_id": "NEW-DEV-99",
            "city": "Hyderabad",
            "country": "IN",
            "amount": 2500.0,
            "timestamp": datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc),
        },
        user_profile=profile,
        known_devices=[Device(id="dev1", device_id="OLD-DEV-1")],
    )
    dev_res = DeviceChangeRule().evaluate(ctx)
    time_res = UnusualTimeRule().evaluate(ctx)

    assessment = AccountTakeoverDetector().evaluate(ctx, [dev_res, time_res])
    assert assessment.signal_count == 1
    assert assessment.risk_level == RiskLevel.LOW
    assert assessment.is_at_risk is False


def test_ato_scenario_3_new_device_plus_unusual_time():
    """Scenario 3: New device + unusual time -> Medium ATO risk."""
    profile = UserBehaviourProfile(
        user_id="U_SCEN3",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["OLD-DEV-1"],
        known_locations=["Hyderabad, IN"],
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        average_transaction_amount=3000.0,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={
            "user_id": "U_SCEN3",
            "device_id": "NEW-DEV-99",
            "city": "Hyderabad",
            "country": "IN",
            "amount": 2500.0,
            "timestamp": datetime(2026, 1, 1, 3, 15, tzinfo=timezone.utc),
        },
        user_profile=profile,
        known_devices=[Device(id="dev1", device_id="OLD-DEV-1")],
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    dev_res = DeviceChangeRule().evaluate(ctx)
    time_res = UnusualTimeRule().evaluate(ctx)

    assessment = AccountTakeoverDetector().evaluate(ctx, [dev_res, time_res])
    assert assessment.signal_count == 2
    assert assessment.risk_level == RiskLevel.MEDIUM
    assert assessment.is_at_risk is True


def test_ato_scenario_4_new_device_new_location_unusual_time():
    """Scenario 4: New device + new location + unusual time -> High ATO risk."""
    profile = UserBehaviourProfile(
        user_id="U_SCEN4",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["OLD-DEV-1"],
        known_locations=["Hyderabad, IN"],
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        average_transaction_amount=3000.0,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={
            "user_id": "U_SCEN4",
            "device_id": "NEW-DEV-99",
            "city": "London",
            "country": "UK",
            "amount": 2500.0,
            "timestamp": datetime(2026, 1, 1, 3, 15, tzinfo=timezone.utc),
        },
        user_profile=profile,
        known_devices=[Device(id="dev1", device_id="OLD-DEV-1")],
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    dev_res = DeviceChangeRule().evaluate(ctx)
    time_res = UnusualTimeRule().evaluate(ctx)

    assessment = AccountTakeoverDetector().evaluate(ctx, [dev_res, time_res])
    assert assessment.signal_count == 3
    assert assessment.risk_level == RiskLevel.HIGH
    assert assessment.is_at_risk is True


def test_ato_scenario_5_full_takeover_pattern():
    """Scenario 5: New device + new location + unusual time + failed login + unusual amount -> CRITICAL ATO risk."""
    profile = UserBehaviourProfile(
        user_id="U_SCEN5",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["OLD-DEV-1"],
        known_locations=["Hyderabad, IN"],
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        average_transaction_amount=3000.0,
        recent_failed_login_count=4,
        profile_transaction_count=20,
    )
    ctx = RuleContext(
        current_transaction={
            "user_id": "U_SCEN5",
            "device_id": "ATTACKER-DEV-666",
            "city": "Bucharest",
            "country": "RO",
            "amount": 90000.0,
            "timestamp": datetime(2026, 1, 1, 2, 45, tzinfo=timezone.utc),
        },
        user_profile=profile,
        known_devices=[Device(id="dev1", device_id="OLD-DEV-1")],
        custom_parameters={"UNUSUAL_TIME_BUFFER_HOURS": 0},
    )
    dev_res = DeviceChangeRule().evaluate(ctx)
    time_res = UnusualTimeRule().evaluate(ctx)
    amt_res = UnusualTransactionAmountRule().evaluate(ctx)

    assessment = AccountTakeoverDetector().evaluate(ctx, [dev_res, time_res, amt_res])
    assert assessment.signal_count == 5
    assert assessment.risk_level == RiskLevel.CRITICAL
    assert assessment.is_at_risk is True
    assert "Potential account takeover risk is CRITICAL" in assessment.explanation


# ---------------------------------------------------------------------------
# 5. API ENDPOINT TESTS
# ---------------------------------------------------------------------------

def test_api_ato_endpoint_existing_user(client: TestClient, db_session: Session):
    user = User(id="api_ato_u1", username="ato_u1", email="ato1@test.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    response = client.get(f"/api/users/{user.id}/account-takeover-risk")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert "risk_level" in data
    assert "signal_count" in data
    assert "signals" in data
    assert "explanation" in data


def test_api_ato_endpoint_user_not_found(client: TestClient):
    response = client.get("/api/users/non_existent_ato_user/account-takeover-risk")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"

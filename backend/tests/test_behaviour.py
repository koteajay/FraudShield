"""Comprehensive Unit, Property, and Integration Tests for Phase 5 User Behaviour Profile."""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, TransactionStatus, RiskLevel
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.login_attempt import LoginAttempt

from app.behaviour.models import (
    ProfileStatus,
    LocationSummary,
    DeviceSummary,
    MerchantSummary,
    AmountRange,
    TimeWindow,
    UserBehaviourProfile,
    BehaviourComparison,
)
from app.behaviour.calculator import BehaviourProfileCalculator
from app.behaviour.service import UserBehaviourProfileService

from app.fraud.context import RuleContext
from app.fraud.engine import FraudRuleEngine
from app.fraud import create_default_engine
from app.fraud.rules.unusual_amount import UnusualTransactionAmountRule
from app.fraud.rules.device_change import DeviceChangeRule
from app.fraud.rules.unusual_time import UnusualTimeRule
from app.fraud.rules.unusual_merchant import UnusualMerchantRule


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides isolated in-memory SQLite database session using StaticPool."""
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
# 1. AMOUNT CALCULATIONS
# ---------------------------------------------------------------------------

def test_amount_no_history():
    calc = BehaviourProfileCalculator()
    avg, min_a, max_a, r_min, r_max, amt_range = calc.calculate_amount_metrics([])
    assert avg is None
    assert min_a is None
    assert max_a is None
    assert r_min is None
    assert r_max is None
    assert amt_range is None


def test_amount_single_transaction():
    calc = BehaviourProfileCalculator()
    amounts = [5000.0]
    avg, min_a, max_a, r_min, r_max, amt_range = calc.calculate_amount_metrics(amounts, multiplier=1.5)
    assert avg == 5000.0
    assert min_a == 5000.0
    assert max_a == 5000.0
    assert r_min == 2500.0  # 5000 * 0.5
    assert r_max == 7500.0  # 5000 * 1.5
    assert amt_range.min == 2500.0
    assert amt_range.max == 7500.0


def test_amount_multiple_transactions():
    calc = BehaviourProfileCalculator()
    amounts = [2000.0, 3000.0, 4000.0]
    avg, min_a, max_a, r_min, r_max, amt_range = calc.calculate_amount_metrics(amounts, multiplier=1.5)
    assert avg == 3000.0
    assert min_a == 2000.0
    assert max_a == 4000.0
    assert r_min == 1500.0  # min(2000, 3000 * 0.5)
    assert r_max == 4500.0  # max(4000, 3000 * 1.5)


# ---------------------------------------------------------------------------
# 2. FREQUENCY METRICS
# ---------------------------------------------------------------------------

def test_frequency_zero_history():
    calc = BehaviourProfileCalculator()
    avg_day, active_days, count = calc.calculate_frequency_metrics([], period_days=30)
    assert avg_day == 0.0
    assert active_days == 0
    assert count == 0


def test_frequency_multiple_days():
    calc = BehaviourProfileCalculator()
    now = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    timestamps = [
        now - timedelta(days=1),
        now - timedelta(days=1, hours=2),
        now - timedelta(days=2),
        now - timedelta(days=3),
    ]
    avg_day, active_days, count = calc.calculate_frequency_metrics(timestamps, period_days=10)
    assert active_days == 3
    assert count == 4
    assert avg_day == 0.4


def test_frequency_same_day():
    calc = BehaviourProfileCalculator()
    now = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
    timestamps = [
        now - timedelta(hours=1),
        now - timedelta(hours=2),
        now - timedelta(hours=3),
    ]
    avg_day, active_days, count = calc.calculate_frequency_metrics(timestamps, period_days=5)
    assert active_days == 1
    assert count == 3
    assert avg_day == 0.6


# ---------------------------------------------------------------------------
# 3. TIME METRICS
# ---------------------------------------------------------------------------

def test_time_empty_history():
    calc = BehaviourProfileCalculator()
    start_h, end_h, window = calc.calculate_hours_metrics([])
    assert start_h is None
    assert end_h is None
    assert window is None


def test_time_normal_window():
    calc = BehaviourProfileCalculator()
    base = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    timestamps = [
        base.replace(hour=8),
        base.replace(hour=12),
        base.replace(hour=15),
        base.replace(hour=22),
    ]
    start_h, end_h, window = calc.calculate_hours_metrics(timestamps)
    assert start_h == 8
    assert end_h == 22
    assert window.start == "08:00"
    assert window.end == "22:00"


# ---------------------------------------------------------------------------
# 4. LOCATION METRICS
# ---------------------------------------------------------------------------

def test_locations_empty():
    calc = BehaviourProfileCalculator()
    labels, detailed = calc.calculate_location_metrics([])
    assert labels == []
    assert detailed == []


def test_locations_multiple_and_repeated():
    calc = BehaviourProfileCalculator()
    txns = [
        {"city": "Hyderabad", "country": "IN", "latitude": 17.38, "longitude": 78.48},
        {"city": "Hyderabad", "country": "IN", "latitude": 17.39, "longitude": 78.49},
        {"city": "Bengaluru", "country": "IN", "latitude": 12.97, "longitude": 77.59},
    ]
    labels, detailed = calc.calculate_location_metrics(txns, min_count=1)
    assert len(detailed) == 2
    assert detailed[0].city == "Hyderabad"
    assert detailed[0].transaction_count == 2
    assert detailed[1].city == "Bengaluru"
    assert detailed[1].transaction_count == 1
    assert "Hyderabad, IN" in labels


def test_locations_min_count_filter():
    calc = BehaviourProfileCalculator()
    txns = [
        {"city": "Hyderabad", "country": "IN"},
        {"city": "Hyderabad", "country": "IN"},
        {"city": "Mumbai", "country": "IN"},
    ]
    labels, detailed = calc.calculate_location_metrics(txns, min_count=2)
    assert len(detailed) == 1
    assert detailed[0].city == "Hyderabad"
    assert "Mumbai, IN" not in labels


# ---------------------------------------------------------------------------
# 5. MERCHANT METRICS
# ---------------------------------------------------------------------------

def test_merchants_empty():
    calc = BehaviourProfileCalculator()
    merchants, categories, detailed = calc.calculate_merchant_metrics([])
    assert merchants == []
    assert categories == []
    assert detailed == []


def test_merchants_multiple():
    calc = BehaviourProfileCalculator()
    txns = [
        {"merchant_id": "M1", "merchant_name": "Amazon", "merchant_category": "Shopping"},
        {"merchant_id": "M1", "merchant_name": "Amazon", "merchant_category": "Shopping"},
        {"merchant_id": "M2", "merchant_name": "Swiggy", "merchant_category": "Food"},
    ]
    merchants, categories, detailed = calc.calculate_merchant_metrics(txns)
    assert len(detailed) == 2
    assert detailed[0].merchant_name == "Amazon"
    assert detailed[0].transaction_count == 2
    assert "Shopping" in categories
    assert "Food" in categories


# ---------------------------------------------------------------------------
# 6. DEVICE METRICS
# ---------------------------------------------------------------------------

def test_devices_empty():
    calc = BehaviourProfileCalculator()
    count, ids, fps, detailed = calc.calculate_device_metrics([], [])
    assert count == 0
    assert ids == []
    assert fps == []
    assert detailed == []


def test_devices_multiple():
    calc = BehaviourProfileCalculator()
    d1 = Device(id="D1", fingerprint="fp1", device_type="mobile", browser="Chrome", operating_system="Android")
    d2 = Device(id="D2", fingerprint="fp2", device_type="desktop", browser="Firefox", operating_system="Windows")
    count, ids, fps, detailed = calc.calculate_device_metrics([d1, d2], [])
    assert count == 2
    assert "D1" in ids
    assert "D2" in ids
    assert len(detailed) == 2


# ---------------------------------------------------------------------------
# 7. FAILED LOGIN METRICS
# ---------------------------------------------------------------------------

def test_failed_logins_empty():
    calc = BehaviourProfileCalculator()
    total, recent, latest = calc.calculate_login_metrics([], now=datetime.now(timezone.utc))
    assert total == 0
    assert recent == 0
    assert latest is None


def test_failed_logins_recent_and_old():
    calc = BehaviourProfileCalculator()
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    l1 = LoginAttempt(id="L1", user_id="U1", is_successful=False, timestamp=now - timedelta(minutes=5))
    l2 = LoginAttempt(id="L2", user_id="U1", is_successful=False, timestamp=now - timedelta(minutes=10))
    l3 = LoginAttempt(id="L3", user_id="U1", is_successful=False, timestamp=now - timedelta(hours=2))
    l4 = LoginAttempt(id="L4", user_id="U1", is_successful=True, timestamp=now - timedelta(minutes=1))  # successful
    total, recent, latest = calc.calculate_login_metrics([l1, l2, l3, l4], now=now)
    assert total == 3
    assert recent == 2
    assert latest == l1.timestamp


# ---------------------------------------------------------------------------
# 8. PROFILE STATUS / SUFFICIENCY TIERS
# ---------------------------------------------------------------------------

def test_profile_status_tiers():
    calc = BehaviourProfileCalculator()
    assert calc.determine_profile_status(0) == ProfileStatus.INSUFFICIENT_DATA
    assert calc.determine_profile_status(4) == ProfileStatus.INSUFFICIENT_DATA
    assert calc.determine_profile_status(5) == ProfileStatus.DEVELOPING
    assert calc.determine_profile_status(19) == ProfileStatus.DEVELOPING
    assert calc.determine_profile_status(20) == ProfileStatus.ESTABLISHED
    assert calc.determine_profile_status(50) == ProfileStatus.ESTABLISHED


# ---------------------------------------------------------------------------
# 9. CURRENT TRANSACTION COMPARISON
# ---------------------------------------------------------------------------

def test_comparison_normal_and_unusual():
    profile = UserBehaviourProfile(
        user_id="U100",
        profile_status=ProfileStatus.ESTABLISHED,
        average_transaction_amount=3000.0,
        minimum_transaction_amount=2000.0,
        maximum_transaction_amount=4000.0,
        normal_amount_lower_bound=1500.0,
        normal_amount_upper_bound=4500.0,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=22,
        known_locations=["Hyderabad, India"],
        known_categories=["shopping", "groceries"],
        known_merchants=["Amazon"],
        known_devices=1,
        known_device_ids=["DEV-001"],
        profile_transaction_count=25,
    )

    # Normal transaction
    normal_txn = {
        "amount": 3500.0,
        "city": "Hyderabad",
        "country": "India",
        "device_id": "DEV-001",
        "merchant_name": "Amazon",
        "merchant_category": "shopping",
        "timestamp": datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc),
    }
    comp_normal = profile.compare_transaction(normal_txn)
    assert comp_normal.amount_within_normal_range is True
    assert comp_normal.location_is_known is True
    assert comp_normal.device_is_known is True
    assert comp_normal.merchant_is_known is True
    assert comp_normal.time_is_normal is True
    assert comp_normal.amount_vs_average_ratio == 1.17

    # Unusual transaction
    suspicious_txn = {
        "amount": 50000.0,
        "city": "Moscow",
        "country": "Russia",
        "device_id": "DEV-999",
        "merchant_name": "SuspiciousCasino",
        "merchant_category": "gambling",
        "timestamp": datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc),
    }
    comp_suspicious = profile.compare_transaction(suspicious_txn)
    assert comp_suspicious.amount_within_normal_range is False
    assert comp_suspicious.location_is_known is False
    assert comp_suspicious.device_is_known is False
    assert comp_suspicious.merchant_is_known is False
    assert comp_suspicious.time_is_normal is False
    assert comp_suspicious.amount_vs_average_ratio == 16.67


# ---------------------------------------------------------------------------
# 10. SERVICE & REPOSITORY INTEGRATION
# ---------------------------------------------------------------------------

def test_service_with_database_user(db_session: Session):
    # Setup test user
    user = User(
        id="user_test_100",
        username="john_doe",
        email="john@example.com",
        hashed_password="secret",
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)

    # Setup devices
    device1 = Device(id="dev_1", user_id=user.id, fingerprint="fp1", device_type="mobile")
    db_session.add(device1)

    # Setup 6 transactions in past 10 days
    now = datetime.now(timezone.utc)
    for i in range(6):
        txn = Transaction(
            id=f"tx_{i}",
            user_id=user.id,
            amount=1000.0 * (i + 1),
            currency="INR",
            timestamp=now - timedelta(days=i + 1),
            status=TransactionStatus.APPROVED,
            risk_score=10.0,
            risk_level=RiskLevel.LOW,
            city="Hyderabad",
            country="IN",
            merchant_id="m_amazon",
            merchant_name="Amazon",
            merchant_category="Shopping",
            device_id=device1.id,
        )
        db_session.add(txn)

    # Setup 1 failed login
    login_attempt = LoginAttempt(
        id="login_1",
        user_id=user.id,
        attempted_email=user.email,
        ip_address="127.0.0.1",
        is_successful=False,
        timestamp=now - timedelta(minutes=5),
    )
    db_session.add(login_attempt)
    db_session.commit()

    service = UserBehaviourProfileService(db_session)
    profile = service.get_user_profile(user.id)

    assert profile.user_id == user.id
    assert profile.profile_status == ProfileStatus.DEVELOPING  # 6 transactions
    assert profile.profile_transaction_count == 6
    assert profile.average_transaction_amount == 3500.0
    assert profile.minimum_transaction_amount == 1000.0
    assert profile.maximum_transaction_amount == 6000.0
    assert len(profile.known_locations) == 1
    assert "Hyderabad" in profile.known_locations[0]
    assert profile.known_devices == 1
    assert "dev_1" in profile.known_device_ids
    assert profile.failed_login_count == 1
    assert profile.recent_failed_login_count == 1


def test_service_exclude_current_transaction(db_session: Session):
    user = User(id="user_exclude", username="exclude_me", email="ex@example.com", hashed_password="h", role=UserRole.USER)
    db_session.add(user)

    now = datetime.now(timezone.utc)
    # Historical txn
    t1 = Transaction(id="t_hist", user_id=user.id, amount=1000.0, currency="INR", timestamp=now - timedelta(days=2))
    # Current suspicious txn
    t2 = Transaction(id="t_curr", user_id=user.id, amount=99999.0, currency="INR", timestamp=now)
    db_session.add_all([t1, t2])
    db_session.commit()

    service = UserBehaviourProfileService(db_session)
    # When excluding current txn
    profile = service.get_user_profile(user.id, exclude_transaction_id="t_curr")
    assert profile.profile_transaction_count == 1
    assert profile.average_transaction_amount == 1000.0
    assert profile.maximum_transaction_amount == 1000.0


# ---------------------------------------------------------------------------
# 11. API ENDPOINT TESTS
# ---------------------------------------------------------------------------

def test_api_endpoint_get_behaviour_profile(client: TestClient, db_session: Session):
    user = User(id="api_user_1", username="api_user", email="api@example.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    response = client.get("/api/users/api_user_1/behaviour-profile")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "api_user_1"
    assert data["profile_status"] == "INSUFFICIENT_DATA"
    assert data["average_transaction_amount"] is None
    assert data["known_locations"] == []
    assert data["known_devices"] == 0
    assert data["failed_login_count"] == 0


def test_api_endpoint_user_not_found(client: TestClient, db_session: Session):
    response = client.get("/api/users/non_existent_user_99999/behaviour-profile")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 12. INTEGRATION WITH PHASE 3 RULES VIA RULECONTEXT
# ---------------------------------------------------------------------------

def test_unusual_amount_rule_uses_behaviour_profile():
    rule = UnusualTransactionAmountRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        average_transaction_amount=2000.0,
        profile_transaction_count=10,
    )

    # Current transaction is 10,000 (5x average, threshold is 3x)
    context_triggered = RuleContext(
        current_transaction={"id": "tx_curr", "amount": 10000.0, "user_id": "U1"},
        user_profile=profile,
    )
    res_triggered = rule.evaluate(context_triggered)
    assert res_triggered.triggered is True
    assert res_triggered.evidence["historical_average"] == 2000.0
    assert res_triggered.evidence["comparison_ratio"] == 5.0

    # Current transaction is 2,500 (within normal threshold)
    context_normal = RuleContext(
        current_transaction={"id": "tx_curr", "amount": 2500.0, "user_id": "U1"},
        user_profile=profile,
    )
    res_normal = rule.evaluate(context_normal)
    assert res_normal.triggered is False


def test_device_change_rule_uses_behaviour_profile():
    rule = DeviceChangeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=2,
        known_device_ids=["DEV-001", "DEV-002"],
        known_device_fingerprints=["fp_trusted", "fp_laptop"],
        profile_transaction_count=10,
    )

    # Known device
    ctx_known = RuleContext(
        current_transaction={"device_id": "DEV-001", "device_fingerprint": "fp_trusted"},
        user_profile=profile,
    )
    assert rule.evaluate(ctx_known).triggered is False

    # New device
    ctx_new = RuleContext(
        current_transaction={"device_id": "DEV-999", "device_fingerprint": "fp_unknown"},
        user_profile=profile,
    )
    res_new = rule.evaluate(ctx_new)
    assert res_new.triggered is True
    assert "known_devices_count" in res_new.evidence


def test_unusual_time_rule_uses_behaviour_profile():
    rule = UnusualTimeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        normal_transaction_start_hour=9,
        normal_transaction_end_hour=18,
        profile_transaction_count=15,
    )

    # Transaction at 14:00 (inside normal window 9–18)
    ctx_normal = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)},
        user_profile=profile,
    )
    assert rule.evaluate(ctx_normal).triggered is False

    # Transaction at 02:00 (outside normal window)
    ctx_unusual = RuleContext(
        current_transaction={"timestamp": datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)},
        user_profile=profile,
    )
    res_unusual = rule.evaluate(ctx_unusual)
    assert res_unusual.triggered is True
    assert res_unusual.evidence["historical_min_hour"] == 9
    assert res_unusual.evidence["historical_max_hour"] == 18


def test_unusual_merchant_rule_uses_behaviour_profile():
    rule = UnusualMerchantRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_categories=["groceries", "utilities"],
        known_merchants=["PowerCo"],
        profile_transaction_count=10,
    )

    # Known category
    ctx_known = RuleContext(
        current_transaction={"merchant_category": "Groceries", "merchant_name": "Supermarket"},
        user_profile=profile,
    )
    assert rule.evaluate(ctx_known).triggered is False

    # Unseen category
    ctx_new = RuleContext(
        current_transaction={"merchant_category": "Cryptocurrency", "merchant_name": "CryptoExchange"},
        user_profile=profile,
    )
    res_new = rule.evaluate(ctx_new)
    assert res_new.triggered is True
    assert res_new.evidence["is_new_category"] is True


def test_full_engine_evaluation_with_profile():
    engine = create_default_engine()
    profile = UserBehaviourProfile(
        user_id="U100",
        profile_status=ProfileStatus.ESTABLISHED,
        average_transaction_amount=3000.0,
        normal_transaction_start_hour=8,
        normal_transaction_end_hour=21,
        known_devices=1,
        known_device_ids=["DEV-TRUSTED"],
        known_device_fingerprints=["fp1"],
        known_categories=["groceries"],
        known_merchants=["Supermarket"],
        profile_transaction_count=20,
    )

    # Suspicious transaction triggering amount, time, device, merchant
    context = RuleContext(
        current_transaction={
            "id": "tx_fraud_test",
            "user_id": "U100",
            "amount": 90000.0,
            "timestamp": datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc),
            "device_id": "DEV-UNKNOWN",
            "device_fingerprint": "fp_attacker",
            "merchant_category": "Luxury Watches",
        },
        user_profile=profile,
    )
    results = engine.evaluate(context)
    triggered_ids = {r.rule_id for r in results if r.triggered}

    assert "unusual_transaction_amount" in triggered_ids
    assert "device_change" in triggered_ids
    assert "unusual_time" in triggered_ids
    assert "unusual_merchant" in triggered_ids

"""Unit and Integration Tests for Phase 2 Core Database Models."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models.enums import (
    UserRole,
    RiskLevel,
    TransactionStatus,
    ReviewStatus,
    ReviewState,
    ReviewDecision,
    ReviewPriority,
    FlagSeverity,
    NotificationType,
    NotificationSeverity,
    NotificationChannel,
)
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.review import Review
from app.models.notification import Notification
from app.models.login_attempt import LoginAttempt


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides an isolated in-memory SQLite database session per test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_create_user(db_session: Session):
    """Test User creation with default values, roles, and risk scores."""
    user = User(
        email="test_user@fraudshield.io",
        username="shield_user",
        full_name="Alice Smith",
        phone_number="+15551234567",
        role=UserRole.USER,
        risk_score=15.5,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert len(user.id) == 36
    assert user.email == "test_user@fraudshield.io"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.is_verified is False
    assert user.risk_score == 15.5
    assert user.created_at is not None
    assert "<User id=" in repr(user)


def test_create_device(db_session: Session):
    """Test Device fingerprinting and telemetry tracking."""
    device = Device(
        fingerprint="fp_hash_abcdef1234567890",
        device_type="mobile",
        operating_system="iOS 17.4",
        browser="Safari Mobile 17.4",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X)",
        ip_address="198.51.100.42",
        is_trusted=True,
        is_vpn=False,
        is_tor=False,
        is_emulator=False,
    )
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)

    assert device.id is not None
    assert device.fingerprint == "fp_hash_abcdef1234567890"
    assert device.device_type == "mobile"
    assert device.is_trusted is True
    assert "<Device id=" in repr(device)


def test_create_transaction_with_all_required_store_fields(db_session: Session):
    """
    Test Transaction model storing:
    - Transaction information
    - User information
    - Device information
    - Location
    - Merchant
    - Timestamp
    - Risk score
    - Risk level
    - Triggered rules
    - Review status
    """
    # 1. Create User
    user = User(
        email="shopper@merchant.com",
        username="shopper123",
        full_name="Bob Jones",
    )
    db_session.add(user)
    db_session.commit()

    # 2. Create Device
    device = Device(
        user_id=user.id,
        fingerprint="fp_device_shopper_999",
        device_type="desktop",
        ip_address="203.0.113.195",
    )
    db_session.add(device)
    db_session.commit()

    # 3. Create Transaction with full Location, Merchant, Risk, and Review details
    txn_time = datetime.now(timezone.utc)
    transaction = Transaction(
        transaction_reference="TXN-20260930-001",
        user_id=user.id,
        device_id=device.id,
        # Transaction information
        amount=1499.99,
        currency="USD",
        payment_method="credit_card",
        payment_card_bin="411111",
        payment_card_last4="1111",
        description="High-end Gaming Laptop",
        # Merchant information
        merchant_id="MERCH_TECH_902",
        merchant_name="Apex Electronics Ltd",
        merchant_category="5732_ELECTRONICS",
        # Location information
        ip_address="203.0.113.195",
        country="USA",
        city="San Jose",
        latitude=37.3382,
        longitude=-121.8863,
        billing_country="USA",
        shipping_country="NGA",
        is_billing_shipping_mismatch=True,
        distance_from_last_txn_km=8450.2,
        # Timestamp
        timestamp=txn_time,
        # Risk score and Risk level
        risk_score=87.5,
        risk_level=RiskLevel.HIGH,
        status=TransactionStatus.UNDER_REVIEW,
        # Review status
        review_status=ReviewStatus.PENDING_REVIEW,
        extra_metadata={"ip_risk_score": 75, "ml_model_version": "v2.1"},
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    # 4. Attach Triggered Fraud Rule Results
    rule_res1 = FraudRuleResult(
        transaction_id=transaction.id,
        rule_id="RULE_GEO_CROSS_BORDER_DISCREPANCY",
        rule_name="Billing and Shipping Country Mismatch",
        rule_category="GEO",
        is_triggered=True,
        weight=2.5,
        severity=FlagSeverity.HIGH,
        details={"billing": "USA", "shipping": "NGA"},
        execution_time_ms=1.2,
    )
    rule_res2 = FraudRuleResult(
        transaction_id=transaction.id,
        rule_id="RULE_IMPOSSIBLE_TRAVEL_SPEED",
        rule_name="Unrealistic Geographic Velocity",
        rule_category="GEO",
        is_triggered=True,
        weight=3.0,
        severity=FlagSeverity.CRITICAL,
        details={"distance_km": 8450.2, "elapsed_minutes": 15},
        execution_time_ms=2.1,
    )
    db_session.add_all([rule_res1, rule_res2])

    # 5. Attach Fraud Flags
    flag1 = FraudFlag(
        transaction_id=transaction.id,
        flag_type="CROSS_BORDER_HIGH_RISK",
        severity=FlagSeverity.HIGH,
        reason="Shipping destination country flagged as high-risk cross border mismatch",
        score_impact=40.0,
    )
    flag2 = FraudFlag(
        transaction_id=transaction.id,
        flag_type="IMPOSSIBLE_SPEED",
        severity=FlagSeverity.CRITICAL,
        reason="Speed calculation exceeds commercial flight velocities (approx 33,000 km/h)",
        score_impact=47.5,
    )
    db_session.add_all([flag1, flag2])

    # 6. Attach Review
    review = Review(
        transaction_id=transaction.id,
        status=ReviewState.ASSIGNED,
        priority=ReviewPriority.URGENT,
        notes="Automated queue escalated due to critical speed anomaly",
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(transaction)

    # Assertions
    assert transaction.id is not None
    assert transaction.transaction_reference == "TXN-20260930-001"
    assert transaction.user.email == "shopper@merchant.com"
    assert transaction.device.fingerprint == "fp_device_shopper_999"

    # Location assertions
    assert transaction.country == "USA"
    assert transaction.city == "San Jose"
    assert transaction.latitude == 37.3382
    assert transaction.longitude == -121.8863
    assert transaction.billing_country == "USA"
    assert transaction.shipping_country == "NGA"
    assert transaction.is_billing_shipping_mismatch is True
    assert transaction.distance_from_last_txn_km == 8450.2

    # Merchant assertions
    assert transaction.merchant_id == "MERCH_TECH_902"
    assert transaction.merchant_name == "Apex Electronics Ltd"
    assert transaction.merchant_category == "5732_ELECTRONICS"

    # Risk score and Level assertions
    assert transaction.risk_score == 87.5
    assert transaction.risk_level == RiskLevel.HIGH
    assert transaction.status == TransactionStatus.UNDER_REVIEW

    # Review status assertions
    assert transaction.review_status == ReviewStatus.PENDING_REVIEW
    assert len(transaction.reviews) == 1
    assert transaction.reviews[0].priority == ReviewPriority.URGENT

    # Triggered rules assertions
    assert len(transaction.rule_results) == 2
    assert any(r.rule_id == "RULE_GEO_CROSS_BORDER_DISCREPANCY" for r in transaction.rule_results)
    assert any(r.rule_id == "RULE_IMPOSSIBLE_TRAVEL_SPEED" for r in transaction.rule_results)

    # Flags assertions
    assert len(transaction.fraud_flags) == 2


def test_notification_model(db_session: Session):
    """Test Notification model creation and relationship with User and Transaction."""
    user = User(email="analyst@fraudshield.io", username="fraud_analyst", role=UserRole.ANALYST)
    db_session.add(user)
    db_session.commit()

    notification = Notification(
        user_id=user.id,
        notification_type=NotificationType.FRAUD_ALERT,
        title="Critical Suspicious Transfer",
        message="A transaction for $1,499.99 was flagged as impossible speed travel",
        channel=NotificationChannel.IN_APP,
        severity=NotificationSeverity.HIGH,
        metadata_json={"alert_code": "CRIT_001"},
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    assert notification.id is not None
    assert notification.is_read is False
    assert notification.notification_type == NotificationType.FRAUD_ALERT
    assert notification.channel == NotificationChannel.IN_APP
    assert notification.user.username == "fraud_analyst"


def test_login_attempt_model(db_session: Session):
    """Test LoginAttempt model logging authentication telemetry."""
    login = LoginAttempt(
        attempted_email="target_user@example.com",
        ip_address="198.51.100.12",
        country="FRA",
        city="Paris",
        is_successful=False,
        failure_reason="INVALID_PASSWORD",
        risk_score=65.0,
        is_suspicious=True,
    )
    db_session.add(login)
    db_session.commit()
    db_session.refresh(login)

    assert login.id is not None
    assert login.is_successful is False
    assert login.failure_reason == "INVALID_PASSWORD"
    assert login.is_suspicious is True
    assert login.risk_score == 65.0


def test_transaction_cascade_deletion(db_session: Session):
    """Test cascading delete: removing a transaction cleanly cleans up flags, rules, and reviews."""
    user = User(email="test_cascade@example.com", username="cascade_test")
    db_session.add(user)
    db_session.commit()

    txn = Transaction(
        user_id=user.id,
        amount=100.0,
        risk_score=50.0,
        risk_level=RiskLevel.MEDIUM,
    )
    db_session.add(txn)
    db_session.commit()

    flag = FraudFlag(transaction_id=txn.id, flag_type="TEST_FLAG", reason="Test reason")
    rule = FraudRuleResult(transaction_id=txn.id, rule_id="RULE_TEST", rule_name="Test Rule")
    rev = Review(transaction_id=txn.id)
    db_session.add_all([flag, rule, rev])
    db_session.commit()

    txn_id = txn.id
    db_session.delete(txn)
    db_session.commit()

    # Verify children are cascade deleted
    assert db_session.get(Transaction, txn_id) is None
    assert db_session.query(FraudFlag).filter_by(transaction_id=txn_id).count() == 0
    assert db_session.query(FraudRuleResult).filter_by(transaction_id=txn_id).count() == 0
    assert db_session.query(Review).filter_by(transaction_id=txn_id).count() == 0

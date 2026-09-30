"""Unit and Integration Tests for Repository Persistence Layer."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models.enums import (
    UserRole,
    RiskLevel,
    TransactionStatus,
    ReviewStatus,
    ReviewState,
    ReviewPriority,
    FlagSeverity,
    NotificationType,
)
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.review import Review
from app.models.notification import Notification
from app.models.login_attempt import LoginAttempt
from app.repositories.user_repo import UserRepository, DeviceRepository, LoginAttemptRepository
from app.repositories.transaction_repo import (
    TransactionRepository,
    FraudFlagRepository,
    FraudRuleResultRepository,
    ReviewRepository,
)
from app.repositories.notification_repo import NotificationRepository


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides isolated in-memory SQLite database session."""
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


def test_user_repository(db_session: Session):
    """Test UserRepository operations including case-insensitive lookups and risk updates."""
    repo = UserRepository(db_session)

    user = User(
        email="Persistence@Shield.io",
        username="RepoUser",
        full_name="Persistent User",
    )
    created = repo.create(user)
    assert created.id is not None

    # Lookup by email case-insensitively
    found = repo.get_by_email("persistence@shield.io")
    assert found is not None
    assert found.username == "RepoUser"

    # Lookup by username
    found_username = repo.get_by_username("repouser")
    assert found_username is not None

    # Update risk score
    updated = repo.update_risk_score(created.id, 45.2)
    assert updated.risk_score == 45.2

    # Clamping tests
    clamped_high = repo.update_risk_score(created.id, 150.0)
    assert clamped_high.risk_score == 100.0


def test_device_repository_record_or_update(db_session: Session):
    """Test DeviceRepository creating on first sight and updating on subsequent sight."""
    repo = DeviceRepository(db_session)

    # 1. First sight
    dev1 = repo.record_or_update(
        fingerprint="fp_unique_101",
        device_type="mobile",
        browser="Safari",
        is_vpn=False,
    )
    assert dev1.id is not None
    assert dev1.browser == "Safari"
    assert dev1.is_vpn is False

    # 2. Second sight with updated IP and VPN flag detected
    dev2 = repo.record_or_update(
        fingerprint="fp_unique_101",
        ip_address="198.51.100.99",
        is_vpn=True,
    )
    assert dev2.id == dev1.id  # Same record updated
    assert dev2.ip_address == "198.51.100.99"
    assert dev2.is_vpn is True


def test_login_attempt_repository_sliding_window_count(db_session: Session):
    """Test counting failed attempts for brute-force detection."""
    repo = LoginAttemptRepository(db_session)

    # Add 3 recent failed attempts
    for _ in range(3):
        repo.create(
            LoginAttempt(
                attempted_email="victim@domain.com",
                is_successful=False,
                failure_reason="INVALID_PASSWORD",
            )
        )

    # Add 1 successful attempt
    repo.create(
        LoginAttempt(
            attempted_email="victim@domain.com",
            is_successful=True,
        )
    )

    # Add 1 failed attempt for a different user
    repo.create(
        LoginAttempt(
            attempted_email="other@domain.com",
            is_successful=False,
        )
    )

    failed_count = repo.count_failed_attempts("victim@domain.com", since_minutes=15)
    assert failed_count == 3


def test_transaction_repository_queries(db_session: Session):
    """Test TransactionRepository velocity queries, eager loading, and filtering."""
    user_repo = UserRepository(db_session)
    txn_repo = TransactionRepository(db_session)

    user = user_repo.create(User(email="transactor@fraud.com", username="transactor1"))

    # Create 3 transactions for user
    t1 = txn_repo.create(
        Transaction(
            transaction_reference="REF-001",
            user_id=user.id,
            amount=50.0,
            risk_score=10.0,
            risk_level=RiskLevel.LOW,
            status=TransactionStatus.APPROVED,
            review_status=ReviewStatus.NOT_REQUIRED,
        )
    )
    t2 = txn_repo.create(
        Transaction(
            transaction_reference="REF-002",
            user_id=user.id,
            amount=250.0,
            risk_score=75.0,
            risk_level=RiskLevel.HIGH,
            status=TransactionStatus.UNDER_REVIEW,
            review_status=ReviewStatus.PENDING_REVIEW,
        )
    )
    t3 = txn_repo.create(
        Transaction(
            transaction_reference="REF-003",
            user_id=user.id,
            amount=500.0,
            risk_score=92.0,
            risk_level=RiskLevel.CRITICAL,
            status=TransactionStatus.FLAGGED,
            review_status=ReviewStatus.PENDING_REVIEW,
        )
    )

    # Test lookup by reference
    ref_match = txn_repo.get_by_reference("REF-002")
    assert ref_match is not None
    assert ref_match.amount == 250.0

    # Test count & sum in window
    count = txn_repo.count_user_transactions_in_window(user.id, minutes=60)
    assert count == 3

    total_amount = txn_repo.sum_user_amount_in_window(user.id, minutes=60)
    assert total_amount == 800.0

    # Test list_high_risk
    high_risks = txn_repo.list_high_risk(min_risk_score=70.0)
    assert len(high_risks) == 2
    assert high_risks[0].risk_score == 92.0  # Ordered descending

    # Test list_pending_review
    pending = txn_repo.list_pending_review()
    assert len(pending) == 2


def test_notification_repository_mark_read(db_session: Session):
    """Test NotificationRepository listing unread and marking as read."""
    user = User(email="recipient@notify.com", username="recipient")
    db_session.add(user)
    db_session.commit()

    repo = NotificationRepository(db_session)
    n1 = repo.create(
        Notification(
            user_id=user.id,
            notification_type=NotificationType.SUSPICIOUS_TRANSACTION,
            title="Unusual Activity",
            message="Check your recent activity",
        )
    )
    n2 = repo.create(
        Notification(
            user_id=user.id,
            notification_type=NotificationType.NEW_DEVICE_LOGIN,
            title="New Sign-in",
            message="New sign in detected",
        )
    )

    unread = repo.list_unread_by_user(user.id)
    assert len(unread) == 2

    # Mark first notification as read
    assert repo.mark_as_read(n1.id) is True
    assert repo.mark_as_read(n1.id) is False  # Already read

    remaining_unread = repo.list_unread_by_user(user.id)
    assert len(remaining_unread) == 1
    assert remaining_unread[0].id == n2.id

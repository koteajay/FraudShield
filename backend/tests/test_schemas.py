"""Unit Tests for Pydantic V2 Persistence Schemas."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas import (
    UserCreate,
    UserResponse,
    DeviceCreate,
    DeviceResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionDetailResponse,
    FraudFlagCreate,
    FraudRuleResultCreate,
    ReviewCreate,
    ReviewUpdate,
    NotificationCreate,
    LoginAttemptCreate,
    RiskLevel,
    TransactionStatus,
    ReviewStatus,
    ReviewState,
    ReviewDecision,
    FlagSeverity,
)


def test_user_schema_validation():
    """Verify User validation and invalid inputs rejection."""
    valid_user = UserCreate(
        email="analyst@shield.com",
        username="analyst1",
        full_name="John Analyst",
    )
    assert valid_user.email == "analyst@shield.com"

    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", username="valid_name")

    # Invalid short username
    with pytest.raises(ValidationError):
        UserCreate(email="user@test.com", username="ab")


def test_transaction_schema_validation():
    """Verify Transaction schemas enforce constraints and store all fields."""
    txn_data = TransactionCreate(
        user_id="user_12345",
        amount=250.75,
        currency="USD",
        payment_method="credit_card",
        payment_card_bin="550000",
        payment_card_last4="4444",
        merchant_id="M_99",
        merchant_name="FastPay Store",
        merchant_category="5311_DEPARTMENT_STORE",
        ip_address="192.0.2.1",
        country="USA",
        city="New York",
        latitude=40.7128,
        longitude=-74.0060,
        billing_country="USA",
        shipping_country="CAN",
        is_billing_shipping_mismatch=True,
        distance_from_last_txn_km=450.0,
    )
    assert txn_data.amount == 250.75
    assert txn_data.merchant_name == "FastPay Store"
    assert txn_data.is_billing_shipping_mismatch is True

    # Zero or negative amount rejected
    with pytest.raises(ValidationError):
        TransactionCreate(user_id="u1", amount=0.0)

    with pytest.raises(ValidationError):
        TransactionCreate(user_id="u1", amount=-50.0)


def test_transaction_detail_response_serialization():
    """Verify comprehensive detail response schema serialization."""
    now = datetime.now(timezone.utc)
    detail = TransactionDetailResponse(
        id="txn_abc123",
        transaction_reference="TXN-XYZ",
        user_id="user_456",
        amount=99.99,
        currency="USD",
        payment_method="debit_card",
        timestamp=now,
        created_at=now,
        updated_at=now,
        risk_score=15.0,
        risk_level=RiskLevel.LOW,
        status=TransactionStatus.APPROVED,
        review_status=ReviewStatus.NOT_REQUIRED,
        fraud_flags=[],
        rule_results=[],
        reviews=[],
    )
    assert detail.id == "txn_abc123"
    assert detail.risk_level == RiskLevel.LOW
    assert len(detail.rule_results) == 0

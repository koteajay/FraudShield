"""Unit Tests for All 8 Independent Fraud Rules."""

import pytest
from datetime import datetime, timedelta, timezone

from app.fraud.context import RuleContext
from app.fraud.rules.velocity import TransactionVelocityRule
from app.fraud.rules.unusual_amount import UnusualTransactionAmountRule
from app.fraud.rules.impossible_location import ImpossibleGeographicalLocationRule, haversine_distance_km
from app.fraud.rules.device_change import DeviceChangeRule
from app.fraud.rules.unusual_time import UnusualTimeRule
from app.fraud.rules.failed_login import MultipleFailedLoginRule
from app.fraud.rules.unusual_merchant import UnusualMerchantRule
from app.fraud.rules.blacklisted_country import BlacklistedCountryRule


# ---------------------------------------------------------------------------
# 1. TRANSACTION VELOCITY RULE TESTS
# ---------------------------------------------------------------------------

def test_velocity_below_threshold():
    rule = TransactionVelocityRule()
    now = datetime.now(timezone.utc)
    # Threshold is 5. We have current + 2 recent = 3 total.
    recent = [
        {"id": "t1", "timestamp": now - timedelta(minutes=1)},
        {"id": "t2", "timestamp": now - timedelta(minutes=2)},
    ]
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "timestamp": now},
        recent_transactions=recent,
        custom_parameters={"VELOCITY_THRESHOLD_COUNT": 5, "VELOCITY_WINDOW_MINUTES": 5},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.rule_id == "transaction_velocity"
    assert result.evidence["transaction_count"] == 3
    assert result.score_contribution == 0.0


def test_velocity_exactly_threshold():
    rule = TransactionVelocityRule()
    now = datetime.now(timezone.utc)
    # Threshold is 5. We have current + 4 recent = 5 total.
    recent = [
        {"id": f"t{i}", "timestamp": now - timedelta(minutes=i)}
        for i in range(1, 5)
    ]
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "timestamp": now},
        recent_transactions=recent,
        custom_parameters={"VELOCITY_THRESHOLD_COUNT": 5, "VELOCITY_WINDOW_MINUTES": 5},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["transaction_count"] == 5


def test_velocity_above_threshold():
    rule = TransactionVelocityRule()
    now = datetime.now(timezone.utc)
    # Threshold is 5. We have current + 5 recent = 6 total (> 5).
    recent = [
        {"id": f"t{i}", "timestamp": now - timedelta(minutes=1)}
        for i in range(1, 6)
    ]
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "timestamp": now},
        recent_transactions=recent,
        custom_parameters={"VELOCITY_THRESHOLD_COUNT": 5, "VELOCITY_WINDOW_MINUTES": 5},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.evidence["transaction_count"] == 6
    assert result.score_contribution == 25.0
    assert "More than 5 transactions occurred within 5 minutes" in result.reason


# ---------------------------------------------------------------------------
# 2. UNUSUAL TRANSACTION AMOUNT RULE TESTS
# ---------------------------------------------------------------------------

def test_unusual_amount_insufficient_history():
    rule = UnusualTransactionAmountRule()
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "amount": 5000.0},
        historical_transactions=[{"id": "h1", "amount": 100.0}],  # Only 1 past txn (min is 3)
        custom_parameters={"UNUSUAL_AMOUNT_MIN_HISTORY": 3},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "Insufficient historical transactions" in result.reason
    assert result.evidence["historical_count"] == 1


def test_unusual_amount_normal_amount():
    rule = UnusualTransactionAmountRule()
    history = [
        {"id": "h1", "amount": 100.0},
        {"id": "h2", "amount": 120.0},
        {"id": "h3", "amount": 80.0},
    ]  # Average = 100.0
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "amount": 150.0},  # 1.5x average (multiplier is 3.0)
        historical_transactions=history,
        custom_parameters={"UNUSUAL_AMOUNT_MULTIPLIER": 3.0, "UNUSUAL_AMOUNT_MIN_HISTORY": 3},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["comparison_ratio"] == 1.5


def test_unusual_amount_suspicious_spike():
    rule = UnusualTransactionAmountRule()
    history = [
        {"id": "h1", "amount": 50.0},
        {"id": "h2", "amount": 60.0},
        {"id": "h3", "amount": 40.0},
    ]  # Average = 50.0
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "amount": 1500.0},  # 30x average
        historical_transactions=history,
        custom_parameters={
            "UNUSUAL_AMOUNT_MULTIPLIER": 3.0,
            "UNUSUAL_AMOUNT_MIN_HISTORY": 3,
            "UNUSUAL_AMOUNT_MIN_THRESHOLD": 100.0,
        },
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 30.0
    assert result.evidence["comparison_ratio"] == 30.0
    assert "exceeds 3.0x the historical average" in result.reason


# ---------------------------------------------------------------------------
# 3. IMPOSSIBLE GEOGRAPHICAL LOCATION RULE TESTS
# ---------------------------------------------------------------------------

def test_impossible_location_normal_travel():
    rule = ImpossibleGeographicalLocationRule()
    t1 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 30, 14, 0, 0, tzinfo=timezone.utc)  # 4 hours later

    # Hyderabad (17.3850, 78.4867) to Bengaluru (12.9716, 77.5946) ~500 km in 4 hours = 125 km/h
    prior_txn = {
        "id": "t_prev",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "city": "Hyderabad",
        "country": "IND",
        "timestamp": t1,
    }
    curr_txn = {
        "id": "t_curr",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "city": "Bengaluru",
        "country": "IND",
        "timestamp": t2,
    }
    ctx = RuleContext(
        current_transaction=curr_txn,
        recent_transactions=[prior_txn],
        custom_parameters={"IMPOSSIBLE_TRAVEL_MAX_SPEED_KMH": 900.0},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["required_speed_kmh"] < 900.0
    assert result.evidence["distance_km"] > 450.0


def test_impossible_location_impossible_travel():
    rule = ImpossibleGeographicalLocationRule()
    t1 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 30, 10, 20, 0, tzinfo=timezone.utc)  # 20 minutes later

    # Hyderabad to Delhi (~1250 km) in 20 minutes = 3750 km/h (impossible for commercial travel)
    prior_txn = {
        "id": "t_prev",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "city": "Hyderabad",
        "country": "IND",
        "timestamp": t1,
    }
    curr_txn = {
        "id": "t_curr",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "city": "Delhi",
        "country": "IND",
        "timestamp": t2,
    }
    ctx = RuleContext(
        current_transaction=curr_txn,
        recent_transactions=[prior_txn],
        custom_parameters={"IMPOSSIBLE_TRAVEL_MAX_SPEED_KMH": 900.0},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 35.0
    assert result.evidence["required_speed_kmh"] > 900.0
    assert "Required travel speed" in result.reason


def test_impossible_location_missing_coordinates():
    rule = ImpossibleGeographicalLocationRule()
    ctx = RuleContext(
        current_transaction={"id": "t_curr", "amount": 100.0},  # No lat/lon
        recent_transactions=[],
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "does not provide geographic coordinates" in result.reason


def test_impossible_location_small_time_difference():
    rule = ImpossibleGeographicalLocationRule()
    t1 = datetime(2026, 9, 30, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 30, 10, 0, 1, tzinfo=timezone.utc)  # 1 second later across 500km

    prior_txn = {"id": "t1", "latitude": 17.3850, "longitude": 78.4867, "timestamp": t1}
    curr_txn = {"id": "t2", "latitude": 12.9716, "longitude": 77.5946, "timestamp": t2}
    ctx = RuleContext(current_transaction=curr_txn, recent_transactions=[prior_txn])
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert "Simultaneous transactions detected" in result.reason or "Required travel speed" in result.reason


# ---------------------------------------------------------------------------
# 4. DEVICE CHANGE RULE TESTS
# ---------------------------------------------------------------------------

def test_device_change_known_device():
    rule = DeviceChangeRule()
    known = [
        {"id": "dev_1", "fingerprint": "fp_trusted_phone_123"},
        {"id": "dev_2", "fingerprint": "fp_trusted_laptop_456"},
    ]
    curr_dev = {"id": "dev_1", "fingerprint": "fp_trusted_phone_123"}
    ctx = RuleContext(
        current_transaction={"id": "t1", "device_id": "dev_1"},
        known_devices=known,
        current_device=curr_dev,
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["is_new_device"] is False


def test_device_change_new_unfamiliar_device():
    rule = DeviceChangeRule()
    known = [{"id": "dev_1", "fingerprint": "fp_trusted_phone_123"}]
    curr_dev = {"id": "dev_new", "fingerprint": "fp_unknown_hacker_device"}
    ctx = RuleContext(
        current_transaction={"id": "t1", "device_id": "dev_new"},
        known_devices=known,
        current_device=curr_dev,
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 15.0
    assert result.evidence["is_new_device"] is True
    assert "Transaction originated from an unfamiliar device" in result.reason


# ---------------------------------------------------------------------------
# 5. UNUSUAL TIME RULE TESTS
# ---------------------------------------------------------------------------

def test_unusual_time_insufficient_history():
    rule = UnusualTimeRule()
    ctx = RuleContext(
        current_transaction={"id": "t1", "timestamp": datetime(2026, 9, 30, 3, 15, tzinfo=timezone.utc)},
        historical_transactions=[{"id": "h1", "timestamp": datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)}],
        custom_parameters={"UNUSUAL_TIME_MIN_HISTORY": 5},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "Insufficient historical transactions" in result.reason


def test_unusual_time_normal_time():
    rule = UnusualTimeRule()
    # User normally transacts 09:00 - 17:00
    history = [
        {"id": f"h{i}", "timestamp": datetime(2026, 9, i, 9 + i, 0, tzinfo=timezone.utc)}
        for i in range(1, 6)
    ]
    curr = {"id": "t_curr", "timestamp": datetime(2026, 9, 30, 14, 0, tzinfo=timezone.utc)}
    ctx = RuleContext(
        current_transaction=curr,
        historical_transactions=history,
        custom_parameters={"UNUSUAL_TIME_MIN_HISTORY": 5, "UNUSUAL_TIME_BUFFER_HOURS": 1},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False


def test_unusual_time_suspicious_time():
    rule = UnusualTimeRule()
    # User normally transacts daytime: 09:00 - 18:00
    history = [
        {"id": f"h{i}", "timestamp": datetime(2026, 9, i, 10 + i, 0, tzinfo=timezone.utc)}
        for i in range(1, 6)
    ]
    # Current transaction at 03:15 AM
    curr = {"id": "t_curr", "timestamp": datetime(2026, 9, 30, 3, 15, tzinfo=timezone.utc)}
    ctx = RuleContext(
        current_transaction=curr,
        historical_transactions=history,
        custom_parameters={"UNUSUAL_TIME_MIN_HISTORY": 5, "UNUSUAL_TIME_BUFFER_HOURS": 1},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 10.0
    assert result.evidence["current_hour"] == 3
    assert "outside the user's regular activity hours" in result.reason


# ---------------------------------------------------------------------------
# 6. MULTIPLE FAILED LOGIN RULE TESTS
# ---------------------------------------------------------------------------

def test_failed_login_below_threshold():
    rule = MultipleFailedLoginRule()
    now = datetime.now(timezone.utc)
    attempts = [
        {"is_successful": False, "timestamp": now - timedelta(minutes=2)},
        {"is_successful": True, "timestamp": now - timedelta(minutes=1)},
    ]
    ctx = RuleContext(
        current_transaction={"id": "t1", "timestamp": now},
        login_attempts=attempts,
        custom_parameters={"FAILED_LOGIN_THRESHOLD": 3, "FAILED_LOGIN_WINDOW_MINUTES": 10},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["failed_login_count"] == 1


def test_failed_login_threshold_reached():
    rule = MultipleFailedLoginRule()
    now = datetime.now(timezone.utc)
    attempts = [
        {"is_successful": False, "failure_reason": "INVALID_PASSWORD", "timestamp": now - timedelta(minutes=i)}
        for i in range(1, 4)  # 3 failed
    ]
    ctx = RuleContext(
        current_transaction={"id": "t1", "timestamp": now},
        login_attempts=attempts,
        custom_parameters={"FAILED_LOGIN_THRESHOLD": 3, "FAILED_LOGIN_WINDOW_MINUTES": 10},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 20.0
    assert result.evidence["failed_login_count"] == 3


def test_failed_login_above_threshold():
    rule = MultipleFailedLoginRule()
    now = datetime.now(timezone.utc)
    attempts = [
        {"is_successful": False, "failure_reason": "INVALID_PASSWORD", "timestamp": now - timedelta(minutes=i)}
        for i in range(1, 6)  # 5 failed
    ]
    ctx = RuleContext(
        current_transaction={"id": "t1", "timestamp": now},
        login_attempts=attempts,
        custom_parameters={"FAILED_LOGIN_THRESHOLD": 3, "FAILED_LOGIN_WINDOW_MINUTES": 10},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.evidence["failed_login_count"] == 5


# ---------------------------------------------------------------------------
# 7. UNUSUAL MERCHANT RULE TESTS
# ---------------------------------------------------------------------------

def test_unusual_merchant_insufficient_history():
    rule = UnusualMerchantRule()
    ctx = RuleContext(
        current_transaction={"id": "t1", "merchant_category": "electronics"},
        historical_transactions=[{"merchant_category": "groceries"}],  # Only 1 past (min is 3)
        custom_parameters={"UNUSUAL_MERCHANT_MIN_HISTORY": 3},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "Insufficient historical transactions with merchant data" in result.reason


def test_unusual_merchant_known_category():
    rule = UnusualMerchantRule()
    history = [
        {"merchant_category": "groceries", "merchant_name": "SuperStore"},
        {"merchant_category": "fuel", "merchant_name": "GasStation"},
        {"merchant_category": "restaurants", "merchant_name": "CafeExpress"},
    ]
    ctx = RuleContext(
        current_transaction={"id": "t1", "merchant_category": "groceries"},
        historical_transactions=history,
        custom_parameters={"UNUSUAL_MERCHANT_MIN_HISTORY": 3},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "matches established user profile" in result.reason


def test_unusual_merchant_unusual_category():
    rule = UnusualMerchantRule()
    history = [
        {"merchant_category": "groceries", "merchant_name": "SuperStore"},
        {"merchant_category": "fuel", "merchant_name": "GasStation"},
        {"merchant_category": "restaurants", "merchant_name": "CafeExpress"},
    ]
    ctx = RuleContext(
        current_transaction={"id": "t1", "merchant_category": "Luxury Jewelry", "merchant_name": "Diamond Palace"},
        historical_transactions=history,
        custom_parameters={"UNUSUAL_MERCHANT_MIN_HISTORY": 3},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 15.0
    assert result.evidence["is_new_category"] is True
    assert "Luxury Jewelry" in result.reason


# ---------------------------------------------------------------------------
# 8. BLACKLISTED COUNTRY RULE TESTS
# ---------------------------------------------------------------------------

def test_blacklisted_country_allowed():
    rule = BlacklistedCountryRule()
    ctx = RuleContext(
        current_transaction={"id": "t1", "country": "USA", "billing_country": "USA", "shipping_country": "CAN"},
        custom_parameters={"BLACKLISTED_COUNTRIES": ["PRK", "IRN", "SYR", "CUB", "RUS"]},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.evidence["matched"] is False


def test_blacklisted_country_blocked():
    rule = BlacklistedCountryRule()
    ctx = RuleContext(
        current_transaction={"id": "t1", "country": "PRK", "billing_country": "USA"},
        custom_parameters={"BLACKLISTED_COUNTRIES": ["PRK", "IRN", "SYR", "CUB", "RUS"]},
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 30.0
    assert result.evidence["matched"] is True
    assert "PRK" in result.evidence["matched_countries"]
    assert "restricted country code(s)" in result.reason

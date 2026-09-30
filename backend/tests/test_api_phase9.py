"""Phase 9 Comprehensive REST API Test Suite.

Validates:
- POST /api/transactions (pipeline orchestration, rule execution, risk scoring, ATO, persistence)
- GET /api/transactions (pagination, filtering, sorting)
- GET /api/transactions/{id} (full detail, 404 handling)
- PATCH /api/transactions/{id}/status (review status lifecycle, validation)
- GET /api/users/{id}/profile (user behaviour profile)
- GET /api/users/{id}/journey (user-level journey timeline)
- GET /api/dashboard/stats (reviewer dashboard statistics)
- GET /api/analytics/fraud (fraud distributions and daily trends)
- GET /api/rules & /api/rules/performance (registry inspection & audit statistics)
- Complete End-to-End integration workflow through REST APIs
"""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import get_db, init_db, SessionLocal
from app.main import app
from app.models.device import Device
from app.models.enums import RiskLevel, ReviewStatus, TransactionStatus
from app.models.fraud_rule_result import FraudRuleResult
from app.models.transaction import Transaction
from app.models.user import User


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


def _seed_user(db: Session, user_id: str, email: str = "user@test.com") -> User:
    """Helper to create and commit a user."""
    user = User(
        id=user_id,
        email=f"{user_id}_{email}",
        username=f"usr_{user_id[:8]}",
        full_name="Phase 9 Test User",
    )
    db.merge(user)
    db.commit()
    return user


# ---------------------------------------------------------------------------
# 1. TRANSACTIONS API: POST /api/transactions
# ---------------------------------------------------------------------------

def test_post_transaction_success_and_orchestration(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    payload = {
        "user_id": user_id,
        "amount": 2500.0,
        "currency": "INR",
        "merchant_id": "merch-101",
        "merchant_name": "Amazon India",
        "merchant_category": "Shopping",
        "location": "Hyderabad, IN",
        "city": "Hyderabad",
        "country": "IN",
        "device_id": "dev-trusted-mobile",
        "payment_method": "credit_card",
        "ip_address": "49.205.100.1",
    }

    response = test_client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["user_id"] == user_id
    assert data["amount"] == 2500.0
    assert data["currency"] == "INR"
    assert data["merchant_name"] == "Amazon India"
    assert "risk" in data
    assert "score" in data["risk"]
    assert "level" in data["risk"]
    assert "explanation" in data["risk"]
    assert "device" in data
    assert data["device"]["device_id"] == "dev-trusted-mobile"
    assert "status" in data
    assert "review_status" in data
    assert "account_takeover" in data

    # Verify transaction was persisted in database
    tx_in_db = db_session.query(Transaction).filter(Transaction.id == data["id"]).first()
    assert tx_in_db is not None
    assert tx_in_db.amount == 2500.0

    # Verify FraudRuleResults were persisted for this transaction
    rules_in_db = db_session.query(FraudRuleResult).filter(FraudRuleResult.transaction_id == tx_in_db.id).all()
    assert len(rules_in_db) > 0


def test_post_transaction_validation_error(test_client: TestClient):
    # Missing required 'user_id' and negative amount
    payload = {
        "amount": -50.0,
        "currency": "USD",
    }
    response = test_client.post("/api/transactions", json=payload)
    assert response.status_code == 422


def test_post_suspicious_transaction_triggers_fraud_pipeline(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    # Establish baseline with low amounts
    base_time = datetime(2026, 9, 30, 10, 0, tzinfo=timezone.utc)
    for i in range(5):
        t = Transaction(
            id=str(uuid.uuid4()),
            transaction_reference=f"TXN-BASE-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            amount=1000.0,
            currency="INR",
            city="Hyderabad",
            country="IN",
            timestamp=base_time - timedelta(days=5 - i),
            risk_score=0.0,
            risk_level=RiskLevel.LOW,
        )
        db_session.add(t)
    db_session.commit()

    # Submit massive spike from unfamiliar location and blacklisted country
    payload = {
        "user_id": user_id,
        "amount": 250000.0,  # 250x spike
        "currency": "INR",
        "merchant_name": "Suspicious Gateway",
        "city": "Pyongyang",
        "country": "PRK",  # Blacklisted country
        "device_id": "new-unseen-hacker-box",
        "timestamp": base_time.isoformat(),
    }

    response = test_client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["risk"]["score"] >= 30.0
    assert data["risk"]["level"] in ("HIGH", "CRITICAL")
    assert data["review_status"] == "PENDING_REVIEW"
    assert len(data["triggered_rules"]) >= 1

    triggered_ids = {r["rule_id"] for r in data["triggered_rules"]}
    assert "blacklisted_country" in triggered_ids or "unusual_transaction_amount" in triggered_ids


# ---------------------------------------------------------------------------
# 2. TRANSACTIONS API: GET /api/transactions & GET /api/transactions/{id}
# ---------------------------------------------------------------------------

def test_get_transactions_pagination_and_filters(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    # Create 5 transactions
    for i in range(5):
        t = Transaction(
            id=str(uuid.uuid4()),
            transaction_reference=f"TXN-PAG-{uuid.uuid4().hex[:6]}",
            user_id=user_id,
            amount=100.0 * (i + 1),
            currency="USD",
            merchant_name="Filtered Merchant" if i % 2 == 0 else "Other Merchant",
            risk_score=20.0 * (i + 1),
            risk_level=RiskLevel.HIGH if i >= 3 else RiskLevel.LOW,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=i * 5),
        )
        db_session.add(t)
    db_session.commit()

    # Pagination test: page=1, page_size=2
    resp_pag = test_client.get(f"/api/transactions?user_id={user_id}&page=1&page_size=2")
    assert resp_pag.status_code == 200
    data_pag = resp_pag.json()
    assert data_pag["page"] == 1
    assert data_pag["page_size"] == 2
    assert len(data_pag["items"]) == 2
    assert data_pag["total"] == 5
    assert data_pag["total_pages"] == 3

    # Filter by risk_level=HIGH
    resp_filt = test_client.get(f"/api/transactions?user_id={user_id}&risk_level=HIGH")
    assert resp_filt.status_code == 200
    data_filt = resp_filt.json()
    assert data_filt["total"] == 2

    # Filter by merchant
    resp_merch = test_client.get(f"/api/transactions?user_id={user_id}&merchant=Filtered")
    assert resp_merch.status_code == 200
    data_merch = resp_merch.json()
    assert data_merch["total"] == 3


def test_get_transaction_detail_and_not_found(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-DET-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=450.0,
        currency="USD",
        risk_score=15.0,
        risk_level=RiskLevel.LOW,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx)
    db_session.commit()

    # Success by ID
    resp_ok = test_client.get(f"/api/transactions/{tx.id}")
    assert resp_ok.status_code == 200
    data_ok = resp_ok.json()
    assert data_ok["id"] == tx.id
    assert data_ok["amount"] == 450.0

    # 404 Not Found
    resp_404 = test_client.get("/api/transactions/nonexistent-txn-id")
    assert resp_404.status_code == 404


# ---------------------------------------------------------------------------
# 3. REVIEW API: PATCH /api/transactions/{id}/status
# ---------------------------------------------------------------------------

def test_patch_transaction_review_status(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-REV-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=999.0,
        currency="USD",
        risk_score=70.0,
        risk_level=RiskLevel.HIGH,
        review_status=ReviewStatus.PENDING_REVIEW,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx)
    db_session.commit()

    # 1. Update status to CLEARED
    resp = test_client.patch(f"/api/transactions/{tx.id}/status", json={"status": "CLEARED"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_review_status"] == "PENDING_REVIEW"
    assert data["review_status"] == "CLEARED"

    # Verify persistence
    db_session.refresh(tx)
    assert tx.review_status == ReviewStatus.CLEARED

    # 2. Update status to ESCALATED
    resp2 = test_client.patch(f"/api/transactions/{tx.id}/status", json={"status": "ESCALATED"})
    assert resp2.status_code == 200
    assert resp2.json()["review_status"] == "ESCALATED"

    # 3. Invalid status should return 400
    resp_bad = test_client.patch(f"/api/transactions/{tx.id}/status", json={"status": "INVALID_RANDOM_STATUS"})
    assert resp_bad.status_code == 400

    # 4. Unknown transaction ID should return 404
    resp_404 = test_client.patch("/api/transactions/unknown-id/status", json={"status": "CLEARED"})
    assert resp_404.status_code == 404


# ---------------------------------------------------------------------------
# 4. USER PROFILE & USER JOURNEY API
# ---------------------------------------------------------------------------

def test_get_user_profile_api(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    # Add baseline transaction
    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-USR-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=1200.0,
        currency="INR",
        city="Bengaluru",
        country="IN",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx)
    db_session.commit()

    # Success
    resp = test_client.get(f"/api/users/{user_id}/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user_id
    assert "average_transaction_amount" in data
    assert "normal_amount_range" in data

    # 404 for unknown user
    resp_404 = test_client.get("/api/users/unknown-user-id/profile")
    assert resp_404.status_code == 404


def test_get_user_journey_api(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-JRN-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=3000.0,
        currency="INR",
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(tx)
    db_session.commit()

    # Valid user journey
    resp = test_client.get(f"/api/users/{user_id}/journey?before_minutes=60&after_minutes=15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user_id
    assert len(data["events"]) >= 1

    # 404 for unknown user
    resp_404 = test_client.get("/api/users/nonexistent-user/journey")
    assert resp_404.status_code == 404

    # Negative window should return 400
    resp_bad = test_client.get(f"/api/users/{user_id}/journey?before_minutes=-5")
    assert resp_bad.status_code == 400


# ---------------------------------------------------------------------------
# 5. DASHBOARD STATS & FRAUD ANALYTICS API
# ---------------------------------------------------------------------------

def test_get_dashboard_stats_api(test_client: TestClient, db_session: Session):
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    _seed_user(db_session, user_id)

    # Seed 2 transactions (one HIGH risk, one LOW risk)
    tx1 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-DSH1-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=100.0,
        risk_score=20.0,
        risk_level=RiskLevel.LOW,
        review_status=ReviewStatus.CLEARED,
        timestamp=datetime.now(timezone.utc),
    )
    tx2 = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-DSH2-{uuid.uuid4().hex[:6]}",
        user_id=user_id,
        amount=5000.0,
        risk_score=80.0,
        risk_level=RiskLevel.HIGH,
        review_status=ReviewStatus.PENDING_REVIEW,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()

    resp = test_client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_transactions"] >= 2
    assert data["pending_review"] >= 1
    assert data["high_risk_transactions"] >= 1
    assert data["average_risk_score"] > 0.0


def test_get_fraud_analytics_api(test_client: TestClient, db_session: Session):
    resp = test_client.get("/api/analytics/fraud")
    assert resp.status_code == 200
    data = resp.json()

    assert "risk_distribution" in data
    assert "LOW" in data["risk_distribution"]
    assert "CRITICAL" in data["risk_distribution"]
    assert "rule_trigger_distribution" in data
    assert "fraud_status_distribution" in data
    assert "daily_activity" in data


# ---------------------------------------------------------------------------
# 6. RULES & RULE PERFORMANCE API
# ---------------------------------------------------------------------------

def test_get_rules_api(test_client: TestClient):
    resp = test_client.get("/api/rules")
    assert resp.status_code == 200
    data = resp.json()

    assert "rules" in data
    assert len(data["rules"]) == 8  # 8 default fraud rules in registry
    rule_ids = {r["rule_id"] for r in data["rules"]}
    assert "transaction_velocity" in rule_ids
    assert "unusual_transaction_amount" in rule_ids
    assert "device_change" in rule_ids
    assert "unusual_time" in rule_ids


def test_get_rule_performance_api(test_client: TestClient):
    resp = test_client.get("/api/rules/performance")
    assert resp.status_code == 200
    data = resp.json()

    assert "rules" in data
    assert len(data["rules"]) >= 8
    for item in data["rules"]:
        assert "rule_id" in item
        assert "trigger_count" in item
        assert "evaluation_count" in item
        assert "trigger_rate" in item
        assert "total_score_contribution" in item


# ---------------------------------------------------------------------------
# 7. COMPLETE END-TO-END REST API INTEGRATION SCENARIO (PROMPT §25)
# ---------------------------------------------------------------------------

def test_complete_end_to_end_rest_api_scenario(test_client: TestClient):
    """
    Executes the comprehensive 16-step integration workflow purely through REST API calls.
    """
    user_id = f"e2e-user-{uuid.uuid4().hex[:8]}"

    # 1. Ingest normal baseline transaction 1
    r1 = test_client.post("/api/transactions", json={
        "user_id": user_id,
        "amount": 1500.0,
        "currency": "INR",
        "merchant_name": "Grocery Store",
        "city": "Hyderabad",
        "country": "IN",
        "device_id": "device-primary-phone",
    })
    assert r1.status_code == 201

    # 2. Ingest normal baseline transaction 2
    r2 = test_client.post("/api/transactions", json={
        "user_id": user_id,
        "amount": 2200.0,
        "currency": "INR",
        "merchant_name": "Coffee Shop",
        "city": "Hyderabad",
        "country": "IN",
        "device_id": "device-primary-phone",
    })
    assert r2.status_code == 201

    # 3. Ingest suspicious transaction with new device and huge amount spike
    r3 = test_client.post("/api/transactions", json={
        "user_id": user_id,
        "amount": 95000.0,
        "currency": "INR",
        "merchant_name": "Crypto Exchange",
        "city": "Pyongyang",
        "country": "PRK",
        "device_id": "device-unrecognized-laptop",
    })
    assert r3.status_code == 201
    susp_data = r3.json()
    susp_id = susp_data["id"]

    # 4. Verify fraud rules executed, risk score generated, ATO evaluated
    assert susp_data["risk"]["score"] >= 30.0
    assert susp_data["risk"]["level"] in ("MEDIUM", "HIGH", "CRITICAL")
    assert susp_data["review_status"] == "PENDING_REVIEW"
    assert susp_data["device"]["is_new"] is True

    # 5. Retrieve the transaction by ID
    r_get = test_client.get(f"/api/transactions/{susp_id}")
    assert r_get.status_code == 200
    assert r_get.json()["id"] == susp_id

    # 6. Retrieve user profile
    r_prof = test_client.get(f"/api/users/{user_id}/profile")
    assert r_prof.status_code == 200
    assert r_prof.json()["user_id"] == user_id

    # 7. Retrieve transaction journey
    r_tx_jrn = test_client.get(f"/api/transactions/{susp_id}/journey")
    assert r_tx_jrn.status_code == 200
    assert len(r_tx_jrn.json()["events"]) >= 3

    # 8. Retrieve user-level journey
    r_usr_jrn = test_client.get(f"/api/users/{user_id}/journey")
    assert r_usr_jrn.status_code == 200
    assert r_usr_jrn.json()["user_id"] == user_id

    # 9. Retrieve dashboard statistics
    r_stats = test_client.get("/api/dashboard/stats")
    assert r_stats.status_code == 200
    assert r_stats.json()["total_transactions"] >= 3

    # 10. Retrieve fraud analytics
    r_an = test_client.get("/api/analytics/fraud")
    assert r_an.status_code == 200
    assert "risk_distribution" in r_an.json()

    # 11. Retrieve rules and rule performance
    r_rules = test_client.get("/api/rules")
    assert r_rules.status_code == 200
    r_perf = test_client.get("/api/rules/performance")
    assert r_perf.status_code == 200

    # 12. Update transaction status to CLEARED
    r_patch = test_client.patch(f"/api/transactions/{susp_id}/status", json={"status": "CLEARED"})
    assert r_patch.status_code == 200
    assert r_patch.json()["review_status"] == "CLEARED"

    # 13. Verify updated status
    r_verify = test_client.get(f"/api/transactions/{susp_id}")
    assert r_verify.status_code == 200
    assert r_verify.json()["review_status"] == "CLEARED"

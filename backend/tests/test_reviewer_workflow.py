"""Tests for Phase 12 Reviewer Workflow, Status Transitions, and Audit History."""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.main import app
from app.models.enums import RiskLevel, ReviewStatus
from app.models.review import Review
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
    return TestClient(app)


def _seed_test_user(db: Session) -> User:
    u_id = f"user-{uuid.uuid4().hex[:8]}"
    user = User(
        id=u_id,
        email=f"{u_id}@test.com",
        username=f"usr_{uuid.uuid4().hex[:12]}",
        full_name="Workflow Test User",
    )
    db.merge(user)
    db.commit()
    return user


def _seed_test_transaction(
    db: Session,
    user_id: str,
    status: ReviewStatus = ReviewStatus.PENDING_REVIEW,
    amount: float = 50000.0,
) -> Transaction:
    tx = Transaction(
        id=str(uuid.uuid4()),
        transaction_reference=f"TXN-WF-{uuid.uuid4().hex[:8].upper()}",
        user_id=user_id,
        amount=amount,
        currency="INR",
        risk_score=85.0,
        risk_level=RiskLevel.HIGH,
        review_status=status,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def test_transition_pending_to_reviewed(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)
    tx = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)

    resp = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "REVIEWED", "note": "Investigated velocity and user history."},
        headers={"X-Reviewer-ID": "analyst-42"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_review_status"] == "PENDING_REVIEW"
    assert data["review_status"] == "REVIEWED"
    assert data["review"] is not None
    assert data["review"]["reviewer_id"] == "analyst-42"
    assert data["review"]["previous_status"] == "PENDING_REVIEW"
    assert data["review"]["new_status"] == "REVIEWED"
    assert data["review"]["note"] == "Investigated velocity and user history."

    # Verify database state
    db_session.refresh(tx)
    assert tx.review_status == ReviewStatus.REVIEWED

    # Verify review record
    review = db_session.query(Review).filter(Review.transaction_id == tx.id).first()
    assert review is not None
    assert review.reviewer_id == "analyst-42"
    assert review.previous_status == "PENDING_REVIEW"
    assert review.new_status == "REVIEWED"
    assert review.note == "Investigated velocity and user history."


def test_transition_reviewed_to_cleared(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)
    tx = _seed_test_transaction(db_session, user.id, ReviewStatus.REVIEWED)

    resp = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "CLEARED", "note": "Customer verified transaction over OTP."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_review_status"] == "REVIEWED"
    assert data["review_status"] == "CLEARED"
    assert data["review"]["reviewer_id"] == "reviewer-demo"
    assert data["review"]["note"] == "Customer verified transaction over OTP."

    db_session.refresh(tx)
    assert tx.review_status == ReviewStatus.CLEARED


def test_transition_direct_pending_to_cleared(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)
    tx = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)

    resp = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "CLEARED", "note": "Immediate whitelist clearance."},
    )
    assert resp.status_code == 200
    assert resp.json()["review_status"] == "CLEARED"

    db_session.refresh(tx)
    assert tx.review_status == ReviewStatus.CLEARED


def test_invalid_transitions_rejected(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)

    # 1. From CLEARED cannot go to REVIEWED or PENDING_REVIEW
    tx_cleared = _seed_test_transaction(db_session, user.id, ReviewStatus.CLEARED)
    resp_rev = test_client.patch(
        f"/api/transactions/{tx_cleared.id}/status",
        json={"status": "REVIEWED"},
    )
    assert resp_rev.status_code == 400
    err_rev = resp_rev.json().get("detail") or resp_rev.json()["error"]["message"]
    assert "already CLEARED" in err_rev

    resp_pending = test_client.patch(
        f"/api/transactions/{tx_cleared.id}/status",
        json={"status": "PENDING_REVIEW"},
    )
    assert resp_pending.status_code == 400

    # 2. Same status transition rejected
    resp_same = test_client.patch(
        f"/api/transactions/{tx_cleared.id}/status",
        json={"status": "CLEARED"},
    )
    assert resp_same.status_code == 400
    err_same = resp_same.json().get("detail") or resp_same.json()["error"]["message"]
    assert "already in status" in err_same

    # 3. REVIEWED cannot move backwards to PENDING_REVIEW
    tx_reviewed = _seed_test_transaction(db_session, user.id, ReviewStatus.REVIEWED)
    resp_back = test_client.patch(
        f"/api/transactions/{tx_reviewed.id}/status",
        json={"status": "PENDING_REVIEW"},
    )
    assert resp_back.status_code == 400
    err_back = resp_back.json().get("detail") or resp_back.json()["error"]["message"]
    assert "Invalid review status transition" in err_back

    # 4. Unknown/invalid status
    resp_bogus = test_client.patch(
        f"/api/transactions/{tx_reviewed.id}/status",
        json={"status": "BOGUS_STATUS_123"},
    )
    assert resp_bogus.status_code == 400
    err_bogus = resp_bogus.json().get("detail") or resp_bogus.json()["error"]["message"]
    assert "Invalid review status" in err_bogus


def test_immutable_review_history_and_ordering(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)
    tx = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)

    # Step 1: PENDING_REVIEW -> REVIEWED
    resp1 = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "REVIEWED", "note": "Step 1: Analyzed device and IP."},
        headers={"X-Reviewer-ID": "analyst-step1"},
    )
    assert resp1.status_code == 200

    # Step 2: REVIEWED -> CLEARED
    resp2 = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "CLEARED", "note": "Step 2: Approved after user voice call."},
        headers={"X-Reviewer-ID": "analyst-step2"},
    )
    assert resp2.status_code == 200

    # Fetch review history via GET endpoint
    hist_resp = test_client.get(f"/api/transactions/{tx.id}/reviews")
    assert hist_resp.status_code == 200
    hist = hist_resp.json()
    assert hist["transaction_id"] == tx.id
    assert len(hist["reviews"]) == 2

    # Newest first ordering:
    # index 0 should be the second action (CLEARED)
    assert hist["reviews"][0]["previous_status"] == "REVIEWED"
    assert hist["reviews"][0]["new_status"] == "CLEARED"
    assert hist["reviews"][0]["reviewer_id"] == "analyst-step2"
    assert hist["reviews"][0]["note"] == "Step 2: Approved after user voice call."

    # index 1 should be the first action (REVIEWED)
    assert hist["reviews"][1]["previous_status"] == "PENDING_REVIEW"
    assert hist["reviews"][1]["new_status"] == "REVIEWED"
    assert hist["reviews"][1]["reviewer_id"] == "analyst-step1"
    assert hist["reviews"][1]["note"] == "Step 1: Analyzed device and IP."


def test_reviewer_notes_validation(test_client: TestClient, db_session: Session):
    user = _seed_test_user(db_session)
    tx = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)

    # 1. Whitespace only note is trimmed to None
    resp = test_client.patch(
        f"/api/transactions/{tx.id}/status",
        json={"status": "REVIEWED", "note": "    "},
    )
    assert resp.status_code == 200
    assert resp.json()["review"]["note"] is None

    # 2. Maximum length note (2000 chars) succeeds
    tx2 = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)
    exact_2000 = "A" * 2000
    resp_max = test_client.patch(
        f"/api/transactions/{tx2.id}/status",
        json={"status": "REVIEWED", "note": exact_2000},
    )
    assert resp_max.status_code == 200
    assert len(resp_max.json()["review"]["note"]) == 2000

    # 3. Exceeding 2000 characters returns 400 or 422 validation error
    tx3 = _seed_test_transaction(db_session, user.id, ReviewStatus.PENDING_REVIEW)
    too_long = "B" * 2001
    resp_overflow = test_client.patch(
        f"/api/transactions/{tx3.id}/status",
        json={"status": "REVIEWED", "note": too_long},
    )
    assert resp_overflow.status_code in (400, 422)


def test_missing_transaction_returns_404(test_client: TestClient):
    bad_id = str(uuid.uuid4())
    resp_patch = test_client.patch(f"/api/transactions/{bad_id}/status", json={"status": "CLEARED"})
    assert resp_patch.status_code == 404

    resp_get = test_client.get(f"/api/transactions/{bad_id}/reviews")
    assert resp_get.status_code == 404

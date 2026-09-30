"""Transactions REST API Router for Ingestion, Querying, and Review Management."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.logging_config import logger
from app.models.device import Device
from app.models.enums import FlagSeverity, RiskLevel, TransactionStatus, ReviewStatus, ReviewState, ReviewDecision
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.login_attempt import LoginAttempt
from app.models.review import Review
from app.models.transaction import Transaction
from app.models.user import User

from app.behaviour.service import UserBehaviourProfileService
from app.devices.service import DeviceService
from app.fraud.context import RuleContext
from app.fraud import create_default_engine
from app.fraud.scoring import RiskScorer, RuleContribution, generate_explanation
from app.security.account_takeover import AccountTakeoverDetector

from app.schemas.api import (
    AccountTakeoverInfo,
    DeviceInfo,
    PaginatedTransactionsResponse,
    ReviewHistoryResponse,
    ReviewRecord,
    ReviewStatusUpdateRequest,
    ReviewStatusUpdateResponse,
    RiskInfo,
    TransactionIngestRequest,
    TransactionIngestResponse,
    TriggeredRuleInfo,
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post(
    "",
    response_model=TransactionIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and Evaluate Transaction",
    description=(
        "Ingests an incoming transaction, evaluates it across the extensible fraud rule engine, "
        "computes explainable risk scoring and account takeover correlation, persists all audit records, "
        "and returns a comprehensive evaluation."
    ),
)
def ingest_transaction(
    payload: TransactionIngestRequest,
    db: Session = Depends(get_db),
) -> TransactionIngestResponse:
    """Orchestrates transaction ingestion, risk evaluation, and database persistence."""
    # 1. Ensure user exists (create lightweight baseline record if cold start)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        user = User(
            id=payload.user_id,
            email=f"{payload.user_id}@fraudshield.local"[:255],
            username=payload.user_id[:100],
            full_name=f"User {payload.user_id}"[:255],
        )
        db.add(user)
        db.commit()

    # 2. Check device recognition state BEFORE registering/updating device
    device_service = DeviceService(db=db)
    is_known_device = False
    if payload.device_id:
        is_known_device = device_service.is_known_device(
            user_id=payload.user_id,
            device_id=payload.device_id,
        )

    # 3. Retrieve user's historical behaviour profile
    profile_service = UserBehaviourProfileService(db)
    user_profile = profile_service.get_user_profile(payload.user_id)

    # 4. Query recent transactions and login attempts for RuleContext
    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == payload.user_id)
        .order_by(Transaction.timestamp.desc())
        .limit(20)
        .all()
    )
    login_attempts = (
        db.query(LoginAttempt)
        .filter(LoginAttempt.user_id == payload.user_id)
        .order_by(LoginAttempt.timestamp.desc())
        .limit(20)
        .all()
    )
    user_devices = (
        db.query(Device)
        .filter(Device.user_id == payload.user_id)
        .all()
    )

    # Parse location fields
    city = payload.city or (payload.location.split(",")[0].strip() if payload.location else None)
    country = payload.country or (
        payload.location.split(",")[-1].strip() if payload.location and "," in payload.location else None
    )

    tx_time = payload.timestamp or datetime.now(timezone.utc)
    if tx_time.tzinfo is None:
        tx_time = tx_time.replace(tzinfo=timezone.utc)

    # 5. Build RuleContext
    current_tx_dict = {
        "id": str(uuid.uuid4()),
        "user_id": payload.user_id,
        "amount": payload.amount,
        "currency": payload.currency,
        "merchant_id": payload.merchant_id,
        "merchant_name": payload.merchant_name,
        "merchant_category": payload.merchant_category,
        "city": city,
        "country": country,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "timestamp": tx_time,
        "device_id": payload.device_id,
        "payment_method": payload.payment_method or "credit_card",
        "ip_address": payload.ip_address,
        "timezone": getattr(user, "timezone", None),
    }

    context = RuleContext(
        current_transaction=current_tx_dict,
        user=user_profile,
        user_profile=user_profile,
        recent_transactions=recent_txs,
        historical_transactions=recent_txs,
        known_devices=user_devices,
        current_device={"device_id": payload.device_id, "is_known": is_known_device}
        if payload.device_id
        else None,
        login_attempts=login_attempts,
    )

    # 6. Evaluate Fraud Rules
    engine = create_default_engine()
    rule_results = engine.evaluate(context)

    # 7. Compute Risk Scoring (Phase 4)
    scorer = RiskScorer()
    risk_assessment = scorer.score(rule_results)

    # 8. Compute Account Takeover Assessment (Phase 7)
    ato_detector = AccountTakeoverDetector()
    ato_assessment = ato_detector.evaluate(context, rule_results)

    # 9. Register / Refresh Device in database (Phase 6 lifecycle order)
    device_record = None
    if payload.device_id:
        device_record, _ = device_service.process_incoming_request(
            user_id=payload.user_id,
            device_id=payload.device_id,
            user_agent=payload.user_agent,
            ip_address=payload.ip_address,
        )

    # 10. Determine review status and transaction gateway status
    if risk_assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        trans_status = TransactionStatus.FLAGGED
        rev_status = ReviewStatus.PENDING_REVIEW
    elif risk_assessment.risk_level == RiskLevel.MEDIUM:
        trans_status = TransactionStatus.UNDER_REVIEW
        rev_status = ReviewStatus.PENDING_REVIEW
    else:
        trans_status = TransactionStatus.APPROVED
        rev_status = ReviewStatus.NOT_REQUIRED

    # 11. Persist Transaction
    db_tx = Transaction(
        id=current_tx_dict["id"],
        user_id=payload.user_id,
        device_id=device_record.id if device_record else None,
        amount=payload.amount,
        currency=payload.currency,
        merchant_id=payload.merchant_id,
        merchant_name=payload.merchant_name,
        merchant_category=payload.merchant_category,
        city=city,
        country=country,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timestamp=tx_time,
        risk_score=risk_assessment.final_score,
        risk_level=risk_assessment.risk_level,
        status=trans_status,
        review_status=rev_status,
        payment_method=payload.payment_method or "credit_card",
        ip_address=payload.ip_address,
    )
    db.add(db_tx)

    # 12. Persist FraudRuleResults
    for r in rule_results:
        db_rule = FraudRuleResult(
            transaction_id=db_tx.id,
            rule_id=r.rule_id,
            rule_name=r.rule_name,
            is_triggered=r.triggered,
            weight=1.0,
            severity=(
                FlagSeverity.HIGH
                if r.score_contribution >= 25
                else (FlagSeverity.MEDIUM if r.score_contribution >= 15 else FlagSeverity.LOW)
            ),
            details={
                "reason": r.reason,
                "evidence": r.evidence,
                "score_contribution": r.score_contribution,
            },
        )
        db.add(db_rule)

    # 13. Persist FraudFlags for triggered rules
    for rc in risk_assessment.rule_contributions:
        db_flag = FraudFlag(
            transaction_id=db_tx.id,
            flag_type=rc.rule_id.upper(),
            severity=FlagSeverity.HIGH if rc.score >= 25 else FlagSeverity.MEDIUM,
            reason=rc.reason or f"Rule '{rc.rule_name}' triggered",
        )
        db.add(db_flag)

    db.commit()
    db.refresh(db_tx)

    # 14. Build Response
    triggered_rule_infos = [
        TriggeredRuleInfo(
            rule_id=rc.rule_id,
            rule_name=rc.rule_name,
            reason=rc.reason,
            score_contribution=rc.score,
            evidence=rc.evidence,
        )
        for rc in risk_assessment.rule_contributions
    ]

    ato_info = AccountTakeoverInfo(
        is_at_risk=ato_assessment.is_at_risk,
        risk_level=(
            ato_assessment.risk_level.value
            if hasattr(ato_assessment.risk_level, "value")
            else str(ato_assessment.risk_level)
        ),
        signal_count=ato_assessment.signal_count,
        signals=ato_assessment.signals,
        explanation=ato_assessment.explanation,
    )

    location_str = payload.location or (
        ", ".join(filter(None, [city, country])) if city or country else None
    )

    return TransactionIngestResponse(
        id=db_tx.id,
        transaction_reference=db_tx.transaction_reference,
        user_id=db_tx.user_id,
        amount=db_tx.amount,
        currency=db_tx.currency,
        merchant_name=db_tx.merchant_name,
        location=location_str,
        timestamp=db_tx.timestamp,
        device=DeviceInfo(
            device_id=payload.device_id,
            is_new=not is_known_device if payload.device_id else False,
        ),
        risk=RiskInfo(
            score=risk_assessment.final_score,
            level=(
                risk_assessment.risk_level.value
                if hasattr(risk_assessment.risk_level, "value")
                else str(risk_assessment.risk_level)
            ),
            explanation=risk_assessment.explanation,
        ),
        triggered_rules=triggered_rule_infos,
        account_takeover=ato_info,
        status=db_tx.status.value if hasattr(db_tx.status, "value") else str(db_tx.status),
        review_status=(
            db_tx.review_status.value
            if hasattr(db_tx.review_status, "value")
            else str(db_tx.review_status)
        ),
    )


@router.get(
    "",
    response_model=PaginatedTransactionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List Transactions with Filtering & Pagination",
    description="Returns a paginated list of transactions filtered by status, risk level, user, date, or amount.",
)
def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(default=None, description="Transaction or review status filter"),
    risk_level: Optional[str] = Query(default=None, description="Risk level filter (LOW, MEDIUM, HIGH, CRITICAL)"),
    user_id: Optional[str] = Query(default=None, description="Owner user identifier"),
    start_date: Optional[datetime] = Query(default=None, description="Start date ISO string"),
    end_date: Optional[datetime] = Query(default=None, description="End date ISO string"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Minimum risk score"),
    max_score: Optional[float] = Query(default=None, ge=0.0, le=100.0, description="Maximum risk score"),
    merchant: Optional[str] = Query(default=None, description="Merchant name substring"),
    location: Optional[str] = Query(default=None, description="Location/city substring"),
    db: Session = Depends(get_db),
) -> PaginatedTransactionsResponse:
    """Retrieve filtered, paginated transactions ordered by newest first."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )

    query = db.query(Transaction)

    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper())
    if status:
        # Match either transaction status or review status
        query = query.filter(
            or_(
                Transaction.status == status.upper(),
                Transaction.review_status == status.upper(),
            )
        )
    if start_date:
        query = query.filter(Transaction.timestamp >= start_date)
    if end_date:
        query = query.filter(Transaction.timestamp <= end_date)
    if min_score is not None:
        query = query.filter(Transaction.risk_score >= min_score)
    if max_score is not None:
        query = query.filter(Transaction.risk_score <= max_score)
    if merchant:
        query = query.filter(Transaction.merchant_name.ilike(f"%{merchant}%"))
    if location:
        query = query.filter(
            or_(
                Transaction.city.ilike(f"%{location}%"),
                Transaction.country.ilike(f"%{location}%"),
            )
        )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    records = (
        query.order_by(Transaction.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for tx in records:
        items.append({
            "id": tx.id,
            "transaction_reference": tx.transaction_reference,
            "user_id": tx.user_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "merchant_name": tx.merchant_name,
            "city": tx.city,
            "country": tx.country,
            "location": ", ".join(filter(None, [tx.city, tx.country])),
            "timestamp": tx.timestamp.isoformat(),
            "risk_score": tx.risk_score,
            "risk_level": tx.risk_level.value if hasattr(tx.risk_level, "value") else str(tx.risk_level),
            "status": tx.status.value if hasattr(tx.status, "value") else str(tx.status),
            "review_status": (
                tx.review_status.value
                if hasattr(tx.review_status, "value")
                else str(tx.review_status)
            ),
        })

    return PaginatedTransactionsResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get Detailed Transaction Information",
    description="Returns complete details for a single transaction including triggered rules and flags.",
)
def get_transaction_detail(
    id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve single transaction with audit details."""
    tx = (
        db.query(Transaction)
        .filter(
            (Transaction.id == id) | (Transaction.transaction_reference == id)
        )
        .options(
            joinedload(Transaction.rule_results),
            joinedload(Transaction.fraud_flags),
            joinedload(Transaction.device),
        )
        .first()
    )

    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{id}' was not found.",
        )

    # Format rule results
    rule_results_data = []
    contributions = []
    for r in tx.rule_results:
        reason = (r.details or {}).get("reason") or (
            f"Rule '{r.rule_name}' was triggered" if r.is_triggered else "Rule conditions not met"
        )
        evidence = (r.details or {}).get("evidence") or {}
        score_contrib = float((r.details or {}).get("score_contribution") or 0.0)

        rule_results_data.append({
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "is_triggered": r.is_triggered,
            "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            "reason": reason,
            "evidence": evidence,
            "score_contribution": score_contrib,
            "details": r.details or {},
        })

        if r.is_triggered:
            contributions.append(
                RuleContribution(
                    rule_id=r.rule_id,
                    rule_name=r.rule_name,
                    score=score_contrib,
                    reason=reason,
                    evidence=evidence,
                )
            )

    explanation = generate_explanation(tx.risk_score, tx.risk_level, contributions)

    # Format fraud flags
    fraud_flags_data = []
    for f in tx.fraud_flags:
        fraud_flags_data.append({
            "id": f.id,
            "flag_type": f.flag_type,
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "reason": f.reason,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        })

    # Device recognition state
    is_new_device = any(
        r.rule_id == "device_change" and r.is_triggered for r in tx.rule_results
    )
    if not is_new_device and tx.device and tx.device.first_seen_at and tx.device.last_seen_at:
        is_new_device = tx.device.first_seen_at == tx.device.last_seen_at

    # Account takeover assessment
    ato_signals = {
        "new_device": is_new_device or any(r.rule_id == "device_change" and r.is_triggered for r in tx.rule_results),
        "new_location": any(r.rule_id in ("impossible_geographical_location", "blacklisted_country") and r.is_triggered for r in tx.rule_results),
        "unusual_time": any(r.rule_id == "unusual_time" and r.is_triggered for r in tx.rule_results),
        "failed_login": any(r.rule_id == "multiple_failed_login" and r.is_triggered for r in tx.rule_results),
        "unusual_transaction": any(r.rule_id in ("unusual_transaction_amount", "transaction_velocity") and r.is_triggered for r in tx.rule_results),
    }
    signal_count = sum(1 for v in ato_signals.values() if v)
    is_at_risk = signal_count >= 2
    ato_level = (
        "CRITICAL"
        if signal_count >= 4
        else ("HIGH" if signal_count >= 3 else ("MEDIUM" if signal_count >= 2 else "LOW"))
    )
    ato_explanation = (
        f"Potential account takeover risk detected because {signal_count} suspicious signals were observed."
        if is_at_risk
        else "No significant compound account takeover pattern detected."
    )

    return {
        "id": tx.id,
        "transaction_reference": tx.transaction_reference,
        "user_id": tx.user_id,
        "amount": tx.amount,
        "currency": tx.currency,
        "merchant_id": tx.merchant_id,
        "merchant_name": tx.merchant_name,
        "merchant_category": tx.merchant_category,
        "location": ", ".join(filter(None, [tx.city, tx.country])),
        "city": tx.city,
        "country": tx.country,
        "latitude": tx.latitude,
        "longitude": tx.longitude,
        "timestamp": tx.timestamp.isoformat(),
        "device": {
            "device_id": tx.device.device_id if tx.device else tx.device_id,
            "browser": tx.device.browser if tx.device else None,
            "operating_system": tx.device.operating_system if tx.device else None,
            "ip_address": tx.device.ip_address if tx.device else tx.ip_address,
            "is_new": is_new_device,
            "is_trusted": tx.device.is_trusted if tx.device else False,
            "first_seen_at": (
                tx.device.first_seen_at.isoformat()
                if tx.device and tx.device.first_seen_at
                else None
            ),
            "last_seen_at": (
                tx.device.last_seen_at.isoformat()
                if tx.device and tx.device.last_seen_at
                else None
            ),
        },
        "risk": {
            "score": tx.risk_score,
            "level": tx.risk_level.value if hasattr(tx.risk_level, "value") else str(tx.risk_level),
            "explanation": explanation,
        },
        "account_takeover": {
            "is_at_risk": is_at_risk,
            "risk_level": ato_level,
            "signal_count": signal_count,
            "signals": ato_signals,
            "explanation": ato_explanation,
        },
        "status": tx.status.value if hasattr(tx.status, "value") else str(tx.status),
        "review_status": (
            tx.review_status.value
            if hasattr(tx.review_status, "value")
            else str(tx.review_status)
        ),
        "triggered_rules": rule_results_data,
        "fraud_flags": fraud_flags_data,
    }


# Valid status transitions for the reviewer workflow (Phase 12)
VALID_STATUS_TRANSITIONS: Dict[str, set] = {
    "PENDING_REVIEW": {"REVIEWED", "CLEARED", "ESCALATED"},
    "NOT_REQUIRED": {"REVIEWED", "CLEARED", "ESCALATED"},
    "UNDER_REVIEW": {"REVIEWED", "CLEARED", "ESCALATED"},
    "IN_REVIEW": {"REVIEWED", "CLEARED", "ESCALATED"},
    "REVIEWED": {"CLEARED", "ESCALATED"},
    "CLEARED": {"ESCALATED"},
    "ESCALATED": {"REVIEWED", "CLEARED"},
}


@router.patch(
    "/{id}/status",
    response_model=ReviewStatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Transaction Review Status",
    description="Validates and updates review status, persists an immutable Review audit record, and updates the transaction atomically.",
)
def update_transaction_status(
    id: str,
    payload: ReviewStatusUpdateRequest,
    x_reviewer_id: Optional[str] = Header(None, alias="X-Reviewer-ID"),
    db: Session = Depends(get_db),
) -> ReviewStatusUpdateResponse:
    """Updates review status of a transaction and persists an auditable Review history record."""
    # 1. Locate target transaction
    tx = db.query(Transaction).filter(
        (Transaction.id == id) | (Transaction.transaction_reference == id)
    ).first()

    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{id}' was not found.",
        )

    # 2. Validate target status
    target_status = payload.status.upper().strip()
    valid_statuses = {s.value for s in ReviewStatus}

    if target_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid review status '{payload.status}'. "
                f"Allowed statuses: {', '.join(sorted(valid_statuses))}"
            ),
        )

    # 3. Determine current status and validate state transition
    prev_status = (
        tx.review_status.value
        if hasattr(tx.review_status, "value")
        else str(tx.review_status)
    )

    if prev_status == target_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is already in status '{target_status}'.",
        )

    allowed_targets = VALID_STATUS_TRANSITIONS.get(prev_status, set())
    if target_status not in allowed_targets:
        if prev_status == "CLEARED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is already CLEARED and cannot be reopened as REVIEWED or PENDING_REVIEW.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review status transition from '{prev_status}' to '{target_status}'.",
        )

    # 4. Validate and sanitize reviewer note
    cleaned_note: Optional[str] = None
    if payload.note is not None:
        stripped = payload.note.strip()
        if len(stripped) > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviewer note exceeds maximum length of 2000 characters.",
            )
        cleaned_note = stripped if stripped else None

    # 5. Determine reviewer identity (development fallback "reviewer-demo")
    reviewer = (
        x_reviewer_id.strip()
        if x_reviewer_id and x_reviewer_id.strip()
        else "reviewer-demo"
    )

    # 6. Atomic persistence of Review audit record and Transaction status
    now_utc = datetime.now(timezone.utc)
    review_record = Review(
        id=str(uuid.uuid4()),
        transaction_id=tx.id,
        reviewer_id=reviewer,
        previous_status=prev_status,
        new_status=target_status,
        note=cleaned_note,
        notes=cleaned_note,
        status=ReviewState.CLOSED if target_status == "CLEARED" else ReviewState.IN_PROGRESS,
        created_at=now_utc,
        updated_at=now_utc,
    )

    try:
        db.add(review_record)
        tx.review_status = ReviewStatus(target_status)
        tx.updated_at = now_utc
        db.commit()
        db.refresh(tx)
        db.refresh(review_record)
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to atomically record review and update transaction status: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction status due to a database persistence error.",
        )

    return ReviewStatusUpdateResponse(
        id=tx.id,
        transaction_reference=tx.transaction_reference,
        previous_review_status=prev_status,
        review_status=target_status,
        updated_at=tx.updated_at,
        review=ReviewRecord(
            id=review_record.id,
            transaction_id=review_record.transaction_id,
            reviewer_id=review_record.reviewer_id or reviewer,
            previous_status=review_record.previous_status or prev_status,
            new_status=review_record.new_status or target_status,
            note=review_record.note,
            created_at=review_record.created_at,
        ),
    )


@router.get(
    "/{id}/reviews",
    response_model=ReviewHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Transaction Review History",
    description="Returns the complete, immutable review history for the given transaction, ordered newest first.",
)
def get_transaction_reviews(
    id: str,
    db: Session = Depends(get_db),
) -> ReviewHistoryResponse:
    """Returns the complete review audit trail for a transaction, sorted newest first."""
    tx = db.query(Transaction).filter(
        (Transaction.id == id) | (Transaction.transaction_reference == id)
    ).first()

    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{id}' was not found.",
        )

    reviews = (
        db.query(Review)
        .filter(Review.transaction_id == tx.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    review_items = [
        ReviewRecord(
            id=r.id,
            transaction_id=r.transaction_id,
            reviewer_id=r.reviewer_id or "reviewer-demo",
            previous_status=r.previous_status or "PENDING_REVIEW",
            new_status=r.new_status or (r.status.value if hasattr(r.status, "value") else str(r.status)),
            note=r.note or r.notes,
            created_at=r.created_at,
        )
        for r in reviews
    ]

    return ReviewHistoryResponse(
        transaction_id=tx.id,
        reviews=review_items,
    )

"""Transactions REST API Router for Ingestion, Querying, and Review Management."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.device import Device
from app.models.enums import FlagSeverity, RiskLevel, TransactionStatus, ReviewStatus
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.login_attempt import LoginAttempt
from app.models.transaction import Transaction
from app.models.user import User

from app.behaviour.service import UserBehaviourProfileService
from app.devices.service import DeviceService
from app.fraud.context import RuleContext
from app.fraud import create_default_engine
from app.fraud.scoring import RiskScorer
from app.security.account_takeover import AccountTakeoverDetector

from app.schemas.api import (
    AccountTakeoverInfo,
    DeviceInfo,
    PaginatedTransactionsResponse,
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
    for r in tx.rule_results:
        rule_results_data.append({
            "rule_id": r.rule_id,
            "rule_name": r.rule_name,
            "is_triggered": r.is_triggered,
            "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            "details": r.details or {},
        })

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
        },
        "risk": {
            "score": tx.risk_score,
            "level": tx.risk_level.value if hasattr(tx.risk_level, "value") else str(tx.risk_level),
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


@router.patch(
    "/{id}/status",
    response_model=ReviewStatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Transaction Review Status",
    description="Updates the review status (e.g. CLEARED, REVIEWED, PENDING_REVIEW, ESCALATED) of a transaction.",
)
def update_transaction_status(
    id: str,
    payload: ReviewStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> ReviewStatusUpdateResponse:
    """Updates review status of a transaction."""
    tx = db.query(Transaction).filter(
        (Transaction.id == id) | (Transaction.transaction_reference == id)
    ).first()

    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{id}' was not found.",
        )

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

    prev_status = tx.review_status.value if hasattr(tx.review_status, "value") else str(tx.review_status)
    tx.review_status = ReviewStatus(target_status)
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tx)

    return ReviewStatusUpdateResponse(
        id=tx.id,
        transaction_reference=tx.transaction_reference,
        previous_review_status=prev_status,
        review_status=target_status,
        updated_at=tx.updated_at,
    )

"""Dashboard Statistics REST API Router."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.enums import RiskLevel, ReviewStatus
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.transaction import Transaction
from app.schemas.api import DashboardStatsResponse

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get High-Level Reviewer Dashboard Statistics",
    description="Provides real-time aggregate volume metrics, review queue counts, and risk distribution metrics.",
)
def get_dashboard_stats(
    start_date: Optional[datetime] = Query(default=None, description="Filter statistics from start date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter statistics up to end date"),
    db: Session = Depends(get_db),
) -> DashboardStatsResponse:
    """Calculate aggregate dashboard KPIs using database aggregation."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )

    tx_query = db.query(Transaction)
    dev_query = db.query(Device)
    flag_query = db.query(FraudFlag)

    if start_date:
        tx_query = tx_query.filter(Transaction.timestamp >= start_date)
        dev_query = dev_query.filter(Device.first_seen_at >= start_date)
        flag_query = flag_query.filter(FraudFlag.created_at >= start_date)

    if end_date:
        tx_query = tx_query.filter(Transaction.timestamp <= end_date)
        dev_query = dev_query.filter(Device.first_seen_at <= end_date)
        flag_query = flag_query.filter(FraudFlag.created_at <= end_date)

    total_transactions = tx_query.count()

    pending_review = tx_query.filter(
        Transaction.review_status == ReviewStatus.PENDING_REVIEW
    ).count()

    high_risk_transactions = tx_query.filter(
        Transaction.risk_level == RiskLevel.HIGH
    ).count()

    critical_risk_transactions = tx_query.filter(
        Transaction.risk_level == RiskLevel.CRITICAL
    ).count()

    cleared_transactions = tx_query.filter(
        or_(
            Transaction.review_status == ReviewStatus.CLEARED,
            Transaction.review_status == ReviewStatus.RESOLVED_LEGITIMATE,
        )
    ).count()

    reviewed_transactions = tx_query.filter(
        or_(
            Transaction.review_status == ReviewStatus.REVIEWED,
            Transaction.review_status == ReviewStatus.RESOLVED_FRAUD,
        )
    ).count()

    # Compute average risk score
    avg_score_raw = (
        tx_query.with_entities(func.avg(Transaction.risk_score)).scalar()
        if total_transactions > 0
        else 0.0
    )
    avg_score = round(float(avg_score_raw or 0.0), 2)

    new_devices = dev_query.count()

    # Account takeover count: flags matching ATO, or transactions with compound risk
    ato_flags_count = flag_query.filter(
        or_(
            FraudFlag.flag_type.ilike("%TAKEOVER%"),
            FraudFlag.flag_type.ilike("%ATO%"),
            FraudFlag.flag_type.ilike("%DEVICE_CHANGE%"),
        )
    ).count()

    return DashboardStatsResponse(
        total_transactions=total_transactions,
        pending_review=pending_review,
        high_risk_transactions=high_risk_transactions,
        critical_risk_transactions=critical_risk_transactions,
        cleared_transactions=cleared_transactions,
        reviewed_transactions=reviewed_transactions,
        average_risk_score=avg_score,
        new_devices=new_devices,
        account_takeover_risk_events=ato_flags_count,
    )

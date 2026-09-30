"""Fraud Analytics REST API Router."""

from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import RiskLevel, ReviewStatus
from app.models.fraud_rule_result import FraudRuleResult
from app.models.transaction import Transaction
from app.schemas.api import (
    DailyActivityItem,
    FraudAnalyticsResponse,
    RuleTriggerDistributionItem,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/fraud",
    response_model=FraudAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Fraud Analytics Distributions & Trends",
    description=(
        "Retrieves aggregated analytical distributions across risk levels, rule trigger frequencies, "
        "case resolution statuses, and chronological daily activity volumes."
    ),
)
def get_fraud_analytics(
    start_date: Optional[datetime] = Query(default=None, description="Start date ISO filter"),
    end_date: Optional[datetime] = Query(default=None, description="End date ISO filter"),
    user_id: Optional[str] = Query(default=None, description="Filter for specific user"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    db: Session = Depends(get_db),
) -> FraudAnalyticsResponse:
    """Computes fraud reporting metrics and activity trends."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date.",
        )

    tx_query = db.query(Transaction)
    rule_query = db.query(FraudRuleResult)

    if start_date:
        tx_query = tx_query.filter(Transaction.timestamp >= start_date)
        rule_query = rule_query.filter(FraudRuleResult.created_at >= start_date)
    if end_date:
        tx_query = tx_query.filter(Transaction.timestamp <= end_date)
        rule_query = rule_query.filter(FraudRuleResult.created_at <= end_date)
    if user_id:
        tx_query = tx_query.filter(Transaction.user_id == user_id)
        # Link rule results to transactions of this user
        subq = db.query(Transaction.id).filter(Transaction.user_id == user_id).subquery()
        rule_query = rule_query.filter(FraudRuleResult.transaction_id.in_(subq))
    if risk_level:
        tx_query = tx_query.filter(Transaction.risk_level == risk_level.upper())

    # 1. Risk distribution
    risk_counts_raw = (
        tx_query.with_entities(Transaction.risk_level, func.count(Transaction.id))
        .group_by(Transaction.risk_level)
        .all()
    )
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for level, count in risk_counts_raw:
        level_str = level.value if hasattr(level, "value") else str(level)
        if level_str in risk_dist:
            risk_dist[level_str] = count

    # 2. Rule trigger distribution
    rule_counts_raw = (
        rule_query.filter(FraudRuleResult.is_triggered == True)  # noqa: E712
        .with_entities(
            FraudRuleResult.rule_id,
            FraudRuleResult.rule_name,
            func.count(FraudRuleResult.id),
        )
        .group_by(FraudRuleResult.rule_id, FraudRuleResult.rule_name)
        .order_by(func.count(FraudRuleResult.id).desc())
        .all()
    )
    rule_trigger_distribution = [
        RuleTriggerDistributionItem(
            rule_id=r_id,
            rule_name=r_name,
            trigger_count=cnt,
        )
        for r_id, r_name, cnt in rule_counts_raw
    ]

    # 3. Fraud / Review status distribution
    status_counts_raw = (
        tx_query.with_entities(Transaction.review_status, func.count(Transaction.id))
        .group_by(Transaction.review_status)
        .all()
    )
    fraud_status_dist: Dict[str, int] = {}
    for st, count in status_counts_raw:
        st_str = st.value if hasattr(st, "value") else str(st)
        fraud_status_dist[st_str] = count

    # 4. Daily activity breakdown
    daily_raw = (
        tx_query.with_entities(
            func.date(Transaction.timestamp).label("tx_date"),
            func.count(Transaction.id).label("total_tx"),
            func.sum(
                case(
                    (Transaction.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]), 1),
                    else_=0,
                )
            ).label("flagged_tx"),
        )
        .group_by(func.date(Transaction.timestamp))
        .order_by(func.date(Transaction.timestamp).asc())
        .all()
    )

    daily_activity = [
        DailyActivityItem(
            date=str(row[0] or datetime.now().date().isoformat()),
            transactions=int(row[1] or 0),
            flagged=int(row[2] or 0),
        )
        for row in daily_raw
    ]

    return FraudAnalyticsResponse(
        risk_distribution=risk_dist,
        rule_trigger_distribution=rule_trigger_distribution,
        fraud_status_distribution=fraud_status_dist,
        daily_activity=daily_activity,
    )

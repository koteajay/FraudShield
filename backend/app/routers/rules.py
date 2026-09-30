"""Fraud Rules REST API Router."""

from typing import Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.fraud import create_default_engine
from app.models.fraud_rule_result import FraudRuleResult
from app.schemas.api import (
    RuleItem,
    RulePerformanceItem,
    RulePerformanceResponse,
    RulesListResponse,
)

router = APIRouter(
    prefix="/rules",
    tags=["Rules"],
)


@router.get(
    "",
    response_model=RulesListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Registered Fraud Detection Rules",
    description="Returns all active heuristic and deterministic fraud detection rules configured in the FraudRuleRegistry.",
)
def list_rules() -> RulesListResponse:
    """Retrieve all active fraud rules directly from the central RuleRegistry."""
    engine = create_default_engine()
    registered_rules = engine.registry.get_rules()

    rule_items = [
        RuleItem(
            rule_id=r.rule_id,
            name=r.name,
            description=r.description,
            enabled=True,
            score_contribution=r.default_score_contribution,
        )
        for r in registered_rules
    ]

    return RulesListResponse(rules=rule_items)


@router.get(
    "/performance",
    response_model=RulePerformanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Rule Execution Performance Statistics",
    description="Computes trigger frequencies, total evaluations, trigger ratios, and score contributions from persisted audit results.",
)
def get_rule_performance(
    db: Session = Depends(get_db),
) -> RulePerformanceResponse:
    """Computes rule triggering metrics based on persisted FraudRuleResult records."""
    # 1. Total evaluations per rule
    eval_counts = (
        db.query(
            FraudRuleResult.rule_id,
            FraudRuleResult.rule_name,
            func.count(FraudRuleResult.id).label("eval_count"),
        )
        .group_by(FraudRuleResult.rule_id, FraudRuleResult.rule_name)
        .all()
    )

    # 2. Trigger counts per rule
    trigger_counts = dict(
        db.query(
            FraudRuleResult.rule_id,
            func.count(FraudRuleResult.id),
        )
        .filter(FraudRuleResult.is_triggered == True)  # noqa: E712
        .group_by(FraudRuleResult.rule_id)
        .all()
    )

    performance_items: List[RulePerformanceItem] = []

    # Map defaults from registry as baseline
    engine = create_default_engine()
    registered_rule_map = {r.rule_id: r for r in engine.registry.get_rules()}

    # Merge database records
    seen_rule_ids = set()
    for rule_id, rule_name, total_evals in eval_counts:
        seen_rule_ids.add(rule_id)
        trig_cnt = trigger_counts.get(rule_id, 0)
        rate = round(trig_cnt / total_evals, 4) if total_evals > 0 else 0.0

        default_score = (
            registered_rule_map[rule_id].default_score_contribution
            if rule_id in registered_rule_map
            else 10.0
        )
        total_score_contrib = trig_cnt * default_score

        performance_items.append(
            RulePerformanceItem(
                rule_id=rule_id,
                rule_name=rule_name,
                trigger_count=trig_cnt,
                evaluation_count=total_evals,
                trigger_rate=rate,
                total_score_contribution=total_score_contrib,
            )
        )

    # If some registered rules have not yet been evaluated, include them with 0 count
    for rule_id, rule_obj in registered_rule_map.items():
        if rule_id not in seen_rule_ids:
            performance_items.append(
                RulePerformanceItem(
                    rule_id=rule_id,
                    rule_name=rule_obj.name,
                    trigger_count=0,
                    evaluation_count=0,
                    trigger_rate=0.0,
                    total_score_contribution=0.0,
                )
            )

    return RulePerformanceResponse(rules=performance_items)

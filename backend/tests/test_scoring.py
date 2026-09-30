"""Comprehensive Unit, Property, and Integration Tests for Phase 4 Risk Scoring."""

import pytest
from app.models.enums import RiskLevel
from app.fraud.result import RuleResult
from app.fraud.scoring.models import RiskAssessment, RuleContribution
from app.fraud.scoring.scorer import RiskScorer
from app.fraud.scoring.explanations import generate_explanation
from app.fraud.context import RuleContext
from app.fraud.engine import FraudRuleEngine
from app.fraud import create_default_engine
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# 1. SCORE CALCULATION TESTS
# ---------------------------------------------------------------------------

def test_score_calculation_no_triggered_rules():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="transaction_velocity",
            rule_name="Transaction Velocity",
            triggered=False,
            reason="Velocity normal",
            score_contribution=0.0,
        ),
        RuleResult(
            rule_id="unusual_transaction_amount",
            rule_name="Unusual Transaction Amount",
            triggered=False,
            reason="Amount normal",
            score_contribution=0.0,
        ),
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 0.0
    assert assessment.risk_level == RiskLevel.LOW
    assert len(assessment.triggered_rules) == 0
    assert len(assessment.rule_contributions) == 0
    assert "low risk score of 0" in assessment.explanation


def test_score_calculation_velocity_only():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="transaction_velocity",
            rule_name="Transaction Velocity",
            triggered=True,
            reason="Rapid burst detected",
            evidence={"transaction_count": 6},
            score_contribution=25.0,
        ),
        RuleResult(
            rule_id="unusual_transaction_amount",
            rule_name="Unusual Transaction Amount",
            triggered=False,
            reason="Amount normal",
        ),
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 25.0
    assert assessment.risk_level == RiskLevel.LOW  # 25 <= 29 is LOW
    assert assessment.triggered_rules == ["transaction_velocity"]
    assert len(assessment.rule_contributions) == 1
    assert assessment.rule_contributions[0].score == 25.0


def test_score_calculation_amount_only():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="unusual_transaction_amount",
            rule_name="Unusual Transaction Amount",
            triggered=True,
            reason="Amount spike 10x",
            evidence={"amount": 5000.0},
            score_contribution=30.0,
        )
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 30.0
    assert assessment.risk_level == RiskLevel.MEDIUM  # 30 is MEDIUM


def test_score_calculation_location_only():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="impossible_geographical_location",
            rule_name="Impossible Geographical Location",
            triggered=True,
            reason="Speed exceeds 1000 km/h",
            evidence={"speed": 1200.0},
            score_contribution=35.0,
        )
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 35.0
    assert assessment.risk_level == RiskLevel.MEDIUM


def test_score_calculation_multiple_rules_sum():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="transaction_velocity",
            rule_name="Transaction Velocity",
            triggered=True,
            reason="Velocity high",
            score_contribution=25.0,
        ),
        RuleResult(
            rule_id="unusual_transaction_amount",
            rule_name="Unusual Transaction Amount",
            triggered=True,
            reason="Amount high",
            score_contribution=30.0,
        ),
    ]
    # 25 + 30 = 55
    assessment = scorer.score(results)
    assert assessment.final_score == 55.0
    assert assessment.risk_level == RiskLevel.MEDIUM
    assert len(assessment.triggered_rules) == 2


def test_score_calculation_capped_at_100():
    scorer = RiskScorer()
    # 25 + 30 + 35 + 20 = 110 -> capped at 100
    results = [
        RuleResult(rule_id="transaction_velocity", rule_name="Velocity", triggered=True, score_contribution=25.0, reason="r1"),
        RuleResult(rule_id="unusual_transaction_amount", rule_name="Amount", triggered=True, score_contribution=30.0, reason="r2"),
        RuleResult(rule_id="impossible_geographical_location", rule_name="Location", triggered=True, score_contribution=35.0, reason="r3"),
        RuleResult(rule_id="multiple_failed_login", rule_name="Login", triggered=True, score_contribution=20.0, reason="r4"),
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 100.0
    assert assessment.risk_level == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# 2. RISK LEVEL BOUNDARY TESTS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "score,expected_level",
    [
        (0.0, RiskLevel.LOW),
        (29.0, RiskLevel.LOW),
        (30.0, RiskLevel.MEDIUM),
        (59.0, RiskLevel.MEDIUM),
        (60.0, RiskLevel.HIGH),
        (79.0, RiskLevel.HIGH),
        (80.0, RiskLevel.CRITICAL),
        (100.0, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_boundaries(score: float, expected_level: RiskLevel):
    scorer = RiskScorer()
    level = scorer.determine_risk_level(score)
    assert level == expected_level


# ---------------------------------------------------------------------------
# 3. EXPLAINABILITY TESTS
# ---------------------------------------------------------------------------

def test_explanation_no_triggered_rules():
    explanation = generate_explanation(0.0, RiskLevel.LOW, [])
    assert "No suspicious rule conditions were triggered" in explanation
    assert "0" in explanation
    assert "low" in explanation.lower()


def test_explanation_one_triggered_rule():
    contrib = RuleContribution(
        rule_id="unusual_transaction_amount",
        rule_name="Unusual Transaction Amount",
        score=30.0,
        reason="Transaction amount exceeded historical spend average by 4x",
        evidence={"comparison_ratio": 4.0},
    )
    explanation = generate_explanation(30.0, RiskLevel.MEDIUM, [contrib])
    assert "MEDIUM" in explanation
    assert "30" in explanation
    assert "Unusual Transaction Amount" in explanation
    assert "exceeded historical spend average by 4x" in explanation


def test_explanation_multiple_triggered_rules():
    contribs = [
        RuleContribution(rule_id="r1", rule_name="Transaction Velocity", score=25.0, reason="Burst", evidence={}),
        RuleContribution(rule_id="r2", rule_name="Unusual Transaction Amount", score=30.0, reason="High", evidence={}),
        RuleContribution(rule_id="r3", rule_name="Impossible Geographical Location", score=35.0, reason="Speed", evidence={}),
    ]
    explanation = generate_explanation(90.0, RiskLevel.CRITICAL, contribs)
    assert "CRITICAL" in explanation
    assert "90" in explanation
    assert "3 suspicious patterns were detected" in explanation
    assert "Transaction Velocity (+25)" in explanation
    assert "Unusual Transaction Amount (+30)" in explanation
    assert "Impossible Geographical Location (+35)" in explanation


def test_evidence_preservation():
    scorer = RiskScorer()
    sample_evidence = {
        "transaction_count": 7,
        "window_minutes": 5,
        "threshold": 5,
    }
    results = [
        RuleResult(
            rule_id="transaction_velocity",
            rule_name="Transaction Velocity",
            triggered=True,
            reason="Rapid transactions",
            evidence=sample_evidence,
            score_contribution=25.0,
        )
    ]
    assessment = scorer.score(results)
    assert "transaction_velocity" in assessment.evidence
    assert assessment.evidence["transaction_velocity"] == sample_evidence
    assert assessment.rule_contributions[0].evidence == sample_evidence


# ---------------------------------------------------------------------------
# 4. SAFETY & DEFENSIVE TESTS
# ---------------------------------------------------------------------------

def test_duplicate_rule_results_do_not_double_count():
    scorer = RiskScorer()
    dup_results = [
        RuleResult(
            rule_id="transaction_velocity",
            rule_name="Transaction Velocity",
            triggered=True,
            reason="Burst 1",
            score_contribution=25.0,
        ),
        RuleResult(
            rule_id="transaction_velocity",  # Duplicate!
            rule_name="Transaction Velocity",
            triggered=True,
            reason="Burst 2",
            score_contribution=25.0,
        ),
    ]
    assessment = scorer.score(dup_results)
    # Should only count once (25, not 50)
    assert assessment.final_score == 25.0
    assert len(assessment.triggered_rules) == 1
    assert len(assessment.rule_contributions) == 1


def test_empty_rule_results_list():
    scorer = RiskScorer()
    assessment = scorer.score([])
    assert assessment.final_score == 0.0
    assert assessment.risk_level == RiskLevel.LOW
    assert len(assessment.triggered_rules) == 0


def test_negative_score_contribution_safely_clamped():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="custom_negative_rule",
            rule_name="Negative Rule",
            triggered=True,
            reason="Negative points supplied",
            score_contribution=-50.0,
        )
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 0.0
    assert assessment.rule_contributions[0].score == 0.0


def test_missing_reason_and_evidence():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id="sparse_rule",
            rule_name="Sparse Rule",
            triggered=True,
            reason="",
            evidence={},
            score_contribution=15.0,
        )
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 15.0
    assert assessment.rule_contributions[0].reason == "Condition met"
    assert assessment.rule_contributions[0].evidence == {}


# ---------------------------------------------------------------------------
# 5. PROPERTY / INVARIANT TESTS
# ---------------------------------------------------------------------------

def test_invariant_non_triggered_rules_contribute_zero():
    scorer = RiskScorer()
    results = [
        RuleResult(
            rule_id=f"rule_{i}",
            rule_name=f"Rule {i}",
            triggered=False,
            reason="Not triggered",
            score_contribution=50.0,  # Even if non-zero, must not be added!
        )
        for i in range(10)
    ]
    assessment = scorer.score(results)
    assert assessment.final_score == 0.0
    assert len(assessment.triggered_rules) == 0
    assert len(assessment.rule_contributions) == 0


def test_invariant_reproducibility():
    scorer = RiskScorer()
    results = [
        RuleResult(rule_id="r1", rule_name="R1", triggered=True, score_contribution=25.0, reason="r1"),
        RuleResult(rule_id="r2", rule_name="R2", triggered=False, score_contribution=30.0, reason="r2"),
    ]
    a1 = scorer.score(results)
    a2 = scorer.score(results)
    assert a1.final_score == a2.final_score
    assert a1.risk_level == a2.risk_level
    assert a1.explanation == a2.explanation
    assert a1.triggered_rules == a2.triggered_rules


# ---------------------------------------------------------------------------
# 6. INTEGRATION WITH PHASE 3
# ---------------------------------------------------------------------------

def test_full_pipeline_integration_phase3_to_phase4():
    """
    End-to-End Pipeline Integration Test:
    RuleContext -> FraudRuleEngine -> List[RuleResult] -> RiskScorer -> RiskAssessment.
    """
    now = datetime.now(timezone.utc)

    # 1. Construct realistic context with velocity spike & blacklisted country
    current_txn = {
        "id": "txn_live_999",
        "amount": 1250.0,
        "country": "PRK",  # Triggers blacklisted country (+30)
        "timestamp": now,
        "payment_method": "credit_card",
        "merchant_category": "retail",
    }

    # 6 recent transactions in the last 2 minutes (Triggers velocity +25)
    recent_txns = [
        {"id": f"t_{i}", "timestamp": now - timedelta(seconds=i * 20), "amount": 100.0}
        for i in range(1, 7)
    ]

    ctx = RuleContext(
        current_transaction=current_txn,
        recent_transactions=recent_txns,
    )

    # 2. Run Phase 3 FraudRuleEngine
    engine = create_default_engine()
    rule_results = engine.evaluate(ctx)
    assert len(rule_results) == 8

    # 3. Pass outputs to Phase 4 RiskScorer
    scorer = RiskScorer()
    assessment = scorer.score(rule_results)

    # 4. Verify score & explainability
    # Velocity (+25) and Blacklisted Country (+30) must trigger -> Total 55.0 (MEDIUM)
    assert "transaction_velocity" in assessment.triggered_rules
    assert "blacklisted_country" in assessment.triggered_rules
    assert assessment.final_score >= 55.0
    assert assessment.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]

    # Verify evidence preserved
    assert "transaction_velocity" in assessment.evidence
    assert assessment.evidence["transaction_velocity"]["transaction_count"] > 5
    assert assessment.evidence["blacklisted_country"]["matched"] is True

    # Verify explanation mentions triggered patterns
    assert "Transaction Velocity" in assessment.explanation
    assert "Blacklisted Country" in assessment.explanation
    assert str(int(assessment.final_score)) in assessment.explanation

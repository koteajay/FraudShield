"""Risk Scoring Service for FraudShield."""

from typing import Dict, List, Optional, Set
from app.config import Settings, get_settings
from app.logging_config import logger
from app.models.enums import RiskLevel
from app.fraud.result import RuleResult
from app.fraud.scoring.models import RiskAssessment, RuleContribution
from app.fraud.scoring.explanations import generate_explanation


class RiskScorer:
    """
    Evaluates individual rule results to compute bounded fraud risk scores,
    determine categorical risk levels, and produce transparent human explanations.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

        # Configurable score weights for standard rules
        self.rule_score_weights: Dict[str, float] = {
            "transaction_velocity": float(self.settings.SCORE_TRANSACTION_VELOCITY),
            "unusual_transaction_amount": float(self.settings.SCORE_UNUSUAL_TRANSACTION_AMOUNT),
            "impossible_geographical_location": float(self.settings.SCORE_IMPOSSIBLE_GEOGRAPHICAL_LOCATION),
            "device_change": float(self.settings.SCORE_DEVICE_CHANGE),
            "unusual_time": float(self.settings.SCORE_UNUSUAL_TIME),
            "multiple_failed_login": float(self.settings.SCORE_MULTIPLE_FAILED_LOGIN),
            "unusual_merchant": float(self.settings.SCORE_UNUSUAL_MERCHANT),
            "blacklisted_country": float(self.settings.SCORE_BLACKLISTED_COUNTRY),
        }

    def determine_risk_level(self, score: float) -> RiskLevel:
        """
        Map a bounded numeric risk score to an categorical RiskLevel.
        LOW:      0.0 - 29.0
        MEDIUM:  30.0 - 59.0
        HIGH:    60.0 - 79.0
        CRITICAL:80.0 - 100.0
        """
        if score <= self.settings.RISK_LOW_MAX:
            return RiskLevel.LOW
        elif score <= self.settings.RISK_MEDIUM_MAX:
            return RiskLevel.MEDIUM
        elif score <= self.settings.RISK_HIGH_MAX:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def score(self, rule_results: List[RuleResult]) -> RiskAssessment:
        """
        Process a list of RuleResult objects into a standardized RiskAssessment.
        Guarantees:
          - Only triggered rules add score points.
          - Duplicate rule results are detected and counted at most once.
          - Negative/malformed scores are safely clamped.
          - The final score is strictly bounded in [0.0, 100.0].
          - All original forensic evidence is preserved untouched.
        """
        logger.debug(f"RiskScorer evaluating {len(rule_results)} rule results")

        seen_rule_ids: Set[str] = set()
        triggered_rules: List[str] = []
        rule_contributions: List[RuleContribution] = []
        consolidated_evidence: Dict[str, Dict] = {}
        raw_score_sum = 0.0

        for res in rule_results:
            if not isinstance(res, RuleResult):
                logger.warning(f"Skipping invalid non-RuleResult item: {type(res)}")
                continue

            # Deduplication check
            if res.rule_id in seen_rule_ids:
                logger.warning(
                    f"Duplicate rule result received for '{res.rule_id}'. Ignoring duplicate."
                )
                continue
            seen_rule_ids.add(res.rule_id)

            # Preserve evidence for auditability
            if res.evidence:
                consolidated_evidence[res.rule_id] = res.evidence

            # Only triggered rules contribute to the final score
            if res.triggered:
                # Use configured score weight if defined, otherwise rule's declared contribution
                configured_weight = self.rule_score_weights.get(res.rule_id)
                points = configured_weight if configured_weight is not None else res.score_contribution

                # Safeguard against negative or invalid scores
                points = max(0.0, float(points))

                raw_score_sum += points
                triggered_rules.append(res.rule_id)

                rule_contributions.append(
                    RuleContribution(
                        rule_id=res.rule_id,
                        rule_name=res.rule_name,
                        score=points,
                        reason=res.reason or "Condition met",
                        evidence=res.evidence or {},
                    )
                )

        # Bounding score strictly between 0.0 and 100.0
        final_score = max(0.0, min(100.0, raw_score_sum))
        risk_level = self.determine_risk_level(final_score)
        explanation = generate_explanation(final_score, risk_level, rule_contributions)

        logger.info(
            f"Risk assessment complete: score={final_score}, level={risk_level.value}, "
            f"triggered={len(triggered_rules)}"
        )

        return RiskAssessment(
            final_score=final_score,
            risk_level=risk_level,
            triggered_rules=triggered_rules,
            rule_contributions=rule_contributions,
            evidence=consolidated_evidence,
            explanation=explanation,
        )

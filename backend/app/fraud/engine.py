"""Fraud Rule Engine coordinating rule execution against domain context."""

from typing import List, Optional
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext
from app.fraud.registry import RuleRegistry
from app.fraud.result import RuleResult
from app.logging_config import logger


class FraudRuleEngine:
    """
    Extensible execution engine for fraud rules.
    Decoupled from rule-specific business logic: operates on any registered FraudRule.
    Does NOT calculate the final aggregate fraud risk score (deferred to Phase 4).
    """

    def __init__(self, registry: Optional[RuleRegistry] = None):
        self.registry = registry or RuleRegistry()

    def evaluate(self, context: RuleContext) -> List[RuleResult]:
        """
        Evaluate all registered rules against the provided domain context.
        Executes each rule in isolation; safely catches and reports exceptions
        without aborting other rules.
        """
        rules: List[FraudRule] = self.registry.get_rules()
        results: List[RuleResult] = []
        triggered_count = 0

        for rule in rules:
            try:
                result = rule.evaluate(context)
                results.append(result)
                if result.triggered:
                    triggered_count += 1
            except Exception as exc:
                logger.error(
                    f"Unhandled error executing fraud rule '{rule.rule_id}': {exc}",
                    exc_info=True,
                )
                # Fail safely: return a standardized non-blocking error result
                error_result = RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    triggered=False,
                    reason=f"Rule evaluation encountered an internal error: {str(exc)}",
                    evidence={"error": str(exc), "status": "failed_safe"},
                    score_contribution=0.0,
                )
                results.append(error_result)

        logger.info(
            f"Evaluated {len(rules)} fraud rules: {triggered_count} triggered"
        )
        return results

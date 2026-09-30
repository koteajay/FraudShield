"""Fraud Detection Rule Engine package for FraudShield."""

from app.fraud.base import FraudRule
from app.fraud.context import RuleContext
from app.fraud.result import RuleResult
from app.fraud.registry import RuleRegistry
from app.fraud.engine import FraudRuleEngine
from app.fraud.rules import (
    TransactionVelocityRule,
    UnusualTransactionAmountRule,
    ImpossibleGeographicalLocationRule,
    DeviceChangeRule,
    UnusualTimeRule,
    MultipleFailedLoginRule,
    UnusualMerchantRule,
    BlacklistedCountryRule,
    get_default_rules,
)

from app.fraud.scoring import (
    RiskAssessment,
    RuleContribution,
    RiskScorer,
    generate_explanation,
)

__all__ = [
    "FraudRule",
    "RuleContext",
    "RuleResult",
    "RuleRegistry",
    "FraudRuleEngine",
    "create_default_engine",
    "get_default_rules",
    "TransactionVelocityRule",
    "UnusualTransactionAmountRule",
    "ImpossibleGeographicalLocationRule",
    "DeviceChangeRule",
    "UnusualTimeRule",
    "MultipleFailedLoginRule",
    "UnusualMerchantRule",
    "BlacklistedCountryRule",
    "RiskAssessment",
    "RuleContribution",
    "RiskScorer",
    "generate_explanation",
]


def create_default_engine() -> FraudRuleEngine:
    """Create and return a FraudRuleEngine initialized with the 8 standard rules."""
    registry = RuleRegistry()
    for rule in get_default_rules():
        registry.register(rule)
    return FraudRuleEngine(registry=registry)

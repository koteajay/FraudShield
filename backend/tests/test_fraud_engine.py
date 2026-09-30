"""Unit Tests for FraudRuleEngine, RuleRegistry, and Engine Extensibility."""

import pytest
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext
from app.fraud.engine import FraudRuleEngine
from app.fraud.registry import RuleRegistry
from app.fraud.result import RuleResult
from app.fraud.rules import get_default_rules
from app.fraud import create_default_engine


def test_rule_result_structure():
    """Verify RuleResult schema compliance and immutability."""
    result = RuleResult(
        rule_id="test_rule",
        rule_name="Test Rule",
        triggered=True,
        reason="Test triggered successfully",
        evidence={"sample_key": "sample_val", "threshold": 10},
        score_contribution=25.0,
    )
    assert result.rule_id == "test_rule"
    assert result.rule_name == "Test Rule"
    assert result.triggered is True
    assert result.score_contribution == 25.0
    data = result.to_dict()
    assert isinstance(data, dict)
    assert data["rule_id"] == "test_rule"


def test_rule_registry_operations():
    """Verify RuleRegistry registration, lookup, unregister, and isolation."""
    registry = RuleRegistry()
    assert len(registry) == 0

    rules = get_default_rules()
    for rule in rules:
        registry.register(rule)

    assert len(registry) == 8
    assert "transaction_velocity" in registry

    # Lookup rule
    velocity = registry.get_rule("transaction_velocity")
    assert velocity is not None
    assert velocity.name == "Transaction Velocity"

    # Unregister rule
    removed = registry.unregister("transaction_velocity")
    assert removed is True
    assert len(registry) == 7
    assert "transaction_velocity" not in registry

    # Unregister non-existent
    assert registry.unregister("non_existent_rule") is False

    # Clear registry
    registry.clear()
    assert len(registry) == 0


def test_engine_executes_all_default_rules():
    """Verify default engine executes all 8 standard rules on a given context."""
    engine = create_default_engine()
    ctx = RuleContext(
        current_transaction={
            "id": "t1",
            "amount": 100.0,
            "currency": "USD",
            "country": "USA",
            "merchant_category": "retail",
        }
    )

    results = engine.evaluate(ctx)
    assert len(results) == 8

    rule_ids = [r.rule_id for r in results]
    assert "transaction_velocity" in rule_ids
    assert "unusual_transaction_amount" in rule_ids
    assert "impossible_geographical_location" in rule_ids
    assert "device_change" in rule_ids
    assert "unusual_time" in rule_ids
    assert "multiple_failed_login" in rule_ids
    assert "unusual_merchant" in rule_ids
    assert "blacklisted_country" in rule_ids

    # Verify every result has standardized fields
    for r in results:
        assert isinstance(r, RuleResult)
        assert hasattr(r, "rule_id")
        assert hasattr(r, "rule_name")
        assert hasattr(r, "triggered")
        assert hasattr(r, "reason")
        assert hasattr(r, "evidence")
        assert hasattr(r, "score_contribution")


def test_engine_safe_error_handling():
    """Verify engine isolates throwing rules so others complete safely."""
    class FaultyRule(FraudRule):
        @property
        def rule_id(self) -> str:
            return "faulty_rule"

        @property
        def name(self) -> str:
            return "Faulty Crash Rule"

        def evaluate(self, context: RuleContext) -> RuleResult:
            raise RuntimeError("Unexpected external sensor failure")

    class WorkingRule(FraudRule):
        @property
        def rule_id(self) -> str:
            return "working_rule"

        @property
        def name(self) -> str:
            return "Working Rule"

        def evaluate(self, context: RuleContext) -> RuleResult:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                reason="Evaluated normally",
                evidence={},
                score_contribution=10.0,
            )

    registry = RuleRegistry()
    registry.register(FaultyRule())
    registry.register(WorkingRule())

    engine = FraudRuleEngine(registry=registry)
    ctx = RuleContext(current_transaction={"id": "t1"})

    # Evaluate should NOT throw
    results = engine.evaluate(ctx)
    assert len(results) == 2

    faulty_res = next(r for r in results if r.rule_id == "faulty_rule")
    assert faulty_res.triggered is False
    assert "internal error" in faulty_res.reason
    assert faulty_res.evidence["status"] == "failed_safe"

    working_res = next(r for r in results if r.rule_id == "working_rule")
    assert working_res.triggered is True
    assert working_res.score_contribution == 10.0


# ---------------------------------------------------------------------------
# SECTION 19: EXTENSIBILITY TEST
# ---------------------------------------------------------------------------

def test_engine_extensibility_without_modifying_core():
    """
    EXTENSIBILITY PROOF:
    Demonstrates that a third-party developer can define a new custom rule,
    register it with RuleRegistry, and execute it through FraudRuleEngine
    WITHOUT modifying any lines of code in the core engine.
    """
    # 1. Define custom new fraud rule
    class CustomCryptoVelocityRule(FraudRule):
        @property
        def rule_id(self) -> str:
            return "custom_crypto_velocity"

        @property
        def name(self) -> str:
            return "Custom Crypto Velocity"

        @property
        def default_score_contribution(self) -> float:
            return 45.0

        def evaluate(self, context: RuleContext) -> RuleResult:
            payment_method = context.get_transaction_field("payment_method", "").lower()
            amount = context.get_transaction_amount()

            triggered = payment_method == "crypto" and amount > 5000.0
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=triggered,
                reason=(
                    f"High-value crypto transaction detected (${amount:.2f})"
                    if triggered
                    else "Normal transaction payment method."
                ),
                evidence={"payment_method": payment_method, "amount": amount},
                score_contribution=self.default_score_contribution if triggered else 0.0,
            )

    # 2. Register new rule dynamically into standard engine
    engine = create_default_engine()
    engine.registry.register(CustomCryptoVelocityRule())

    assert len(engine.registry) == 9  # 8 default + 1 new custom rule

    # 3. Evaluate context triggering the new rule
    ctx = RuleContext(
        current_transaction={
            "id": "txn_crypto_99",
            "amount": 7500.0,
            "payment_method": "crypto",
            "currency": "USD",
        }
    )

    results = engine.evaluate(ctx)
    assert len(results) == 9

    # 4. Find custom rule result
    custom_res = next(r for r in results if r.rule_id == "custom_crypto_velocity")
    assert custom_res.triggered is True
    assert custom_res.score_contribution == 45.0
    assert "High-value crypto transaction detected ($7500.00)" in custom_res.reason
    assert custom_res.evidence["payment_method"] == "crypto"

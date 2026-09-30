"""Rule Registry managing active FraudRule instances."""

from typing import Dict, List, Optional
from app.fraud.base import FraudRule
from app.logging_config import logger


class RuleRegistry:
    """
    In-memory registry storing registered fraud rules.
    Decouples rule storage from engine evaluation.
    """

    def __init__(self):
        self._rules: Dict[str, FraudRule] = {}

    def register(self, rule: FraudRule) -> None:
        """Register a fraud rule instance."""
        if not isinstance(rule, FraudRule):
            raise TypeError(f"Rule must implement FraudRule interface, got {type(rule)}")
        self._rules[rule.rule_id] = rule
        logger.debug(f"Registered fraud rule: {rule.rule_id} ({rule.name})")

    def unregister(self, rule_id: str) -> bool:
        """Remove a rule by ID. Returns True if removed, False if not found."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.debug(f"Unregistered fraud rule: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[FraudRule]:
        """Fetch a specific rule by ID."""
        return self._rules.get(rule_id)

    def get_rules(self) -> List[FraudRule]:
        """Retrieve all currently registered rules in registration order."""
        return list(self._rules.values())

    def clear(self) -> None:
        """Clear all registered rules."""
        self._rules.clear()

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules

"""Abstract Base Class for all Fraud Rules."""

from abc import ABC, abstractmethod
from app.fraud.context import RuleContext
from app.fraud.result import RuleResult


class FraudRule(ABC):
    """
    Contract interface for an independent, explainable fraud detection rule.
    Each rule must:
      - Have a single, clear responsibility.
      - Return a standardized RuleResult.
      - Never invoke another fraud rule directly.
      - Never compute final risk scores.
      - Never directly modify database state.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique machine-readable identifier for the rule."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display title of the rule."""
        pass

    @property
    def description(self) -> str:
        """Overview of what anomalous condition this rule assesses."""
        return ""

    @property
    def default_score_contribution(self) -> float:
        """Default independent risk score contribution when triggered."""
        return 20.0

    @abstractmethod
    def evaluate(self, context: RuleContext) -> RuleResult:
        """
        Evaluate domain context and return standardized RuleResult.
        Must handle missing or insufficient data safely without raising exceptions.
        """
        pass

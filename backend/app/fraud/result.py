"""Standardized Fraud Rule Evaluation Result."""

from typing import Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class RuleResult(BaseModel):
    """
    Standardized, explainable result produced by an individual fraud rule.
    Does NOT calculate the final aggregate risk score (Phase 4).
    """

    rule_id: str = Field(..., description="Unique machine-readable identifier of the rule")
    rule_name: str = Field(..., description="Human-readable rule title")
    triggered: bool = Field(..., description="True if anomalous/fraudulent criteria met")
    reason: str = Field(..., description="Explainable description of the evaluation outcome")
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured forensic metrics, thresholds, and diagnostic signals",
    )
    score_contribution: float = Field(
        default=0.0,
        description="Independent risk score contribution points (0.0 if not triggered)",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule result to standard dictionary representation."""
        return self.model_dump()

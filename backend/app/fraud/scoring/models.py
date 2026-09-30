"""Risk Assessment Domain Models for FraudShield."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import RiskLevel


class RuleContribution(BaseModel):
    """Forensic breakdown of an individual triggered rule's impact on total risk score."""

    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Display title of the rule")
    score: float = Field(..., ge=0.0, description="Points contributed by this rule")
    reason: str = Field(..., description="Explainable description of the triggered condition")
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preserved rule forensic metrics and thresholds",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )


class RiskAssessment(BaseModel):
    """
    Standardized, explainable risk assessment aggregating individual rule outcomes.
    Answers: 'Why did this transaction receive this risk score?'
    """

    final_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Bounded aggregate risk score (0.0 to 100.0)",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Categorical risk tier: LOW, MEDIUM, HIGH, or CRITICAL",
    )
    triggered_rules: List[str] = Field(
        default_factory=list,
        description="Exact identifiers of rules that evaluated to True",
    )
    rule_contributions: List[RuleContribution] = Field(
        default_factory=list,
        description="Itemized point contributions from each triggered rule",
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Consolidated forensic evidence indexed by rule_id",
    )
    explanation: str = Field(
        ...,
        description="Deterministic, human-readable narrative explaining the assessment",
    )

    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize assessment to standard dictionary."""
        return self.model_dump()

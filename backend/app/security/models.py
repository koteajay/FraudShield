"""Domain models for Account Takeover (ATO) Detection."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import RiskLevel


class SignalStatus(str, Enum):
    """Tri-state evaluation for threat signals: confirmed positive, negative, or unknown/insufficient data."""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class AccountTakeoverSignals(BaseModel):
    """Structured flags for the five core ATO signals."""
    new_device: bool = False
    new_location: bool = False
    unusual_time: bool = False
    failed_login: bool = False
    unusual_transaction: bool = False

    model_config = ConfigDict(frozen=True)


class AccountTakeoverAssessment(BaseModel):
    """
    Standardized, explainable assessment indicating potential account takeover risk.
    Correlates device novelty, location anomalies, temporal deviations, failed logins,
    and financial size spikes.
    """

    user_id: str
    transaction_id: Optional[str] = None
    is_at_risk: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    signal_count: int = 0
    signals: Dict[str, bool] = Field(default_factory=dict)
    signal_statuses: Dict[str, SignalStatus] = Field(default_factory=dict)
    triggered_rules: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""

    model_config = ConfigDict(frozen=True)

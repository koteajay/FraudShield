"""Pydantic schemas for Account Takeover (ATO) responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import RiskLevel


class AccountTakeoverResponse(BaseModel):
    """Structured API response for Account Takeover risk assessment."""

    user_id: str
    transaction_id: Optional[str] = None
    is_at_risk: bool
    risk_level: RiskLevel
    signal_count: int
    signals: Dict[str, bool]
    signal_statuses: Dict[str, str]
    triggered_rules: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    explanation: str

    model_config = ConfigDict(from_attributes=True)

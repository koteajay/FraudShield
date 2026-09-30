"""Pydantic schemas for FraudRuleResult entity."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import FlagSeverity


class FraudRuleResultBase(BaseModel):
    """Base schema for evaluated rule result."""
    rule_id: str = Field(..., max_length=64, description="Unique rule code")
    rule_name: str = Field(..., max_length=128, description="Rule display title")
    rule_category: str = Field(default="GENERAL", max_length=64, description="Rule classification")
    is_triggered: bool = Field(default=True, description="Whether condition evaluated to true")
    weight: float = Field(default=1.0, description="Configured rule weight")
    severity: FlagSeverity = Field(default=FlagSeverity.MEDIUM, description="Rule severity")
    details: Optional[Dict[str, Any]] = Field(None, description="Diagnostic parameters and thresholds")
    execution_time_ms: Optional[float] = Field(None, description="Rule execution latency in ms")


class FraudRuleResultCreate(FraudRuleResultBase):
    """Schema for recording rule evaluation for a transaction."""
    transaction_id: str


class FraudRuleResultResponse(FraudRuleResultBase):
    """Response schema for rule evaluation result."""
    id: str
    transaction_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

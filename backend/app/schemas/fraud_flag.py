"""Pydantic schemas for FraudFlag entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import FlagSeverity


class FraudFlagBase(BaseModel):
    """Base schema for fraud flag signal."""
    flag_type: str = Field(..., max_length=64, description="Flag classification code")
    severity: FlagSeverity = Field(default=FlagSeverity.MEDIUM, description="Flag severity")
    reason: str = Field(..., description="Explainable reason text")
    score_impact: float = Field(default=0.0, ge=0.0, description="Risk score addition")
    is_active: bool = Field(default=True)


class FraudFlagCreate(FraudFlagBase):
    """Schema for attaching a fraud flag to a transaction."""
    transaction_id: str


class FraudFlagResponse(FraudFlagBase):
    """Response schema for fraud flag record."""
    id: str
    transaction_id: str
    resolved: bool
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

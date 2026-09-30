"""Pydantic schemas for Review entity."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ReviewState, ReviewDecision, ReviewPriority


class ReviewBase(BaseModel):
    """Base schema for analyst review case."""
    priority: ReviewPriority = Field(default=ReviewPriority.MEDIUM, description="Review urgency")
    notes: Optional[str] = Field(None, description="Investigator notes")


class ReviewCreate(ReviewBase):
    """Schema for creating a review case for a transaction."""
    transaction_id: str = Field(..., description="Transaction requiring review")
    assigned_to_user_id: Optional[str] = Field(None, description="Initial analyst assignee")
    status: ReviewState = Field(default=ReviewState.ASSIGNED)


class ReviewUpdate(BaseModel):
    """Schema for updating review case state or recording decision."""
    assigned_to_user_id: Optional[str] = None
    status: Optional[ReviewState] = None
    decision: Optional[ReviewDecision] = None
    priority: Optional[ReviewPriority] = None
    notes: Optional[str] = None
    resolution_reason: Optional[str] = None
    escalated_to: Optional[str] = None


class ReviewResponse(ReviewBase):
    """Response schema for review case."""
    id: str
    transaction_id: str
    assigned_to_user_id: Optional[str] = None
    status: ReviewState
    decision: Optional[ReviewDecision] = None
    resolution_reason: Optional[str] = None
    escalated_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

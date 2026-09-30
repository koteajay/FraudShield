"""Pydantic schemas for User Behaviour Profile API responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.behaviour.models import ProfileStatus, AmountRange, TimeWindow, LocationSummary, DeviceSummary, MerchantSummary


class UserBehaviourProfileResponse(BaseModel):
    """API response schema for user behavioural baseline."""

    user_id: str
    profile_status: ProfileStatus

    average_transaction_amount: Optional[float] = None
    minimum_transaction_amount: Optional[float] = None
    maximum_transaction_amount: Optional[float] = None
    normal_amount_range: Optional[AmountRange] = None

    average_transactions_per_day: float = 0.0
    total_active_days: int = 0
    profile_transaction_count: int = 0

    normal_transaction_hours: Optional[TimeWindow] = None
    known_locations: List[str] = Field(default_factory=list)
    detailed_locations: List[LocationSummary] = Field(default_factory=list)

    known_merchants: List[str] = Field(default_factory=list)
    known_categories: List[str] = Field(default_factory=list)
    detailed_merchants: List[MerchantSummary] = Field(default_factory=list)

    known_devices: int = 0
    known_device_ids: List[str] = Field(default_factory=list)
    detailed_devices: List[DeviceSummary] = Field(default_factory=list)

    failed_login_count: int = 0
    recent_failed_login_count: int = 0
    latest_failed_login_at: Optional[datetime] = None

    profile_period_days: int = 30
    profile_period_start: Optional[datetime] = None
    profile_period_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BehaviourComparisonResponse(BaseModel):
    """API response schema for transaction behavioural comparison."""

    amount_within_normal_range: bool
    location_is_known: bool
    device_is_known: bool
    merchant_is_known: bool
    time_is_normal: bool
    amount_vs_average_ratio: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

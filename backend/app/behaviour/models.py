"""Domain models for User Behaviour Profile and Transaction Comparison."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProfileStatus(str, Enum):
    """Categorization of behavioural profile confidence based on data sufficiency."""
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    DEVELOPING = "DEVELOPING"
    ESTABLISHED = "ESTABLISHED"


class LocationSummary(BaseModel):
    """Structured location frequency summary."""
    city: Optional[str] = None
    country: Optional[str] = None
    transaction_count: int = Field(default=1, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(frozen=True)


class DeviceSummary(BaseModel):
    """Structured device profile summary."""
    device_id: str
    fingerprint: Optional[str] = None
    device_type: str = "unknown"
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None

    model_config = ConfigDict(frozen=True)


class MerchantSummary(BaseModel):
    """Structured merchant frequency summary."""
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None
    transaction_count: int = Field(default=1, ge=1)

    model_config = ConfigDict(frozen=True)


class AmountRange(BaseModel):
    """Normal transaction amount boundaries."""
    min: float = Field(..., ge=0.0)
    max: float = Field(..., ge=0.0)

    model_config = ConfigDict(frozen=True)


class TimeWindow(BaseModel):
    """Active daily transaction hour window."""
    start: str = Field(..., description="Start hour formatted as HH:00")
    end: str = Field(..., description="End hour formatted as HH:00")
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=0, le=23)

    model_config = ConfigDict(frozen=True)


class UserBehaviourProfile(BaseModel):
    """
    Comprehensive behavioural baseline learned from user's historical transactions,
    locations, devices, merchants, and authentication events.
    """

    user_id: str
    profile_status: ProfileStatus = ProfileStatus.INSUFFICIENT_DATA

    # Amount metrics
    average_transaction_amount: Optional[float] = None
    minimum_transaction_amount: Optional[float] = None
    maximum_transaction_amount: Optional[float] = None
    normal_amount_lower_bound: Optional[float] = None
    normal_amount_upper_bound: Optional[float] = None
    normal_amount_range: Optional[AmountRange] = None

    # Frequency metrics
    average_transactions_per_day: float = 0.0
    total_active_days: int = 0
    profile_transaction_count: int = 0

    # Temporal metrics
    normal_transaction_start_hour: Optional[int] = None
    normal_transaction_end_hour: Optional[int] = None
    normal_transaction_hours: Optional[TimeWindow] = None

    # Geolocation metrics
    known_locations: List[str] = Field(default_factory=list)
    detailed_locations: List[LocationSummary] = Field(default_factory=list)

    # Merchant metrics
    known_merchants: List[str] = Field(default_factory=list)
    known_categories: List[str] = Field(default_factory=list)
    detailed_merchants: List[MerchantSummary] = Field(default_factory=list)

    # Device metrics
    known_devices: int = 0
    known_device_ids: List[str] = Field(default_factory=list)
    known_device_fingerprints: List[str] = Field(default_factory=list)
    detailed_devices: List[DeviceSummary] = Field(default_factory=list)

    # Authentication telemetry
    failed_login_count: int = 0
    recent_failed_login_count: int = 0
    latest_failed_login_at: Optional[datetime] = None

    # Time window metadata
    profile_period_days: int = 30
    profile_period_start: Optional[datetime] = None
    profile_period_end: Optional[datetime] = None

    model_config = ConfigDict(frozen=True)

    def compare_transaction(
        self,
        transaction: Any,
        current_device: Optional[Any] = None,
    ) -> "BehaviourComparison":
        """Convenience method comparing a transaction against this profile."""
        from app.behaviour.calculator import BehaviourProfileCalculator
        return BehaviourProfileCalculator.compare_transaction(self, transaction, current_device)



class BehaviourComparison(BaseModel):
    """Evaluation comparing a single transaction against the user's historical profile."""

    amount_within_normal_range: bool = True
    location_is_known: bool = True
    device_is_known: bool = True
    merchant_is_known: bool = True
    time_is_normal: bool = True
    amount_vs_average_ratio: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

"""Pydantic schemas for Transaction entity."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import RiskLevel, TransactionStatus, ReviewStatus
from app.schemas.fraud_flag import FraudFlagResponse
from app.schemas.fraud_rule_result import FraudRuleResultResponse
from app.schemas.review import ReviewResponse


class LocationData(BaseModel):
    """Encapsulation of geographic telemetry for transactions."""
    ip_address: Optional[str] = Field(None, max_length=45)
    country: Optional[str] = Field(None, max_length=3)
    city: Optional[str] = Field(None, max_length=64)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    billing_country: Optional[str] = Field(None, max_length=3)
    shipping_country: Optional[str] = Field(None, max_length=3)
    is_billing_shipping_mismatch: bool = False
    distance_from_last_txn_km: Optional[float] = None


class MerchantData(BaseModel):
    """Encapsulation of merchant profile information."""
    merchant_id: Optional[str] = Field(None, max_length=64)
    merchant_name: Optional[str] = Field(None, max_length=128)
    merchant_category: Optional[str] = Field(None, max_length=64)


class TransactionBase(BaseModel):
    """Base schema for financial transactions."""
    amount: float = Field(..., gt=0.0, description="Transaction monetary amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO currency code")
    payment_method: str = Field(default="credit_card", max_length=50)
    payment_card_bin: Optional[str] = Field(None, max_length=8)
    payment_card_last4: Optional[str] = Field(None, max_length=4)
    description: Optional[str] = Field(None, max_length=255)

    # Merchant information
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None

    # Location information
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    billing_country: Optional[str] = None
    shipping_country: Optional[str] = None
    is_billing_shipping_mismatch: bool = False
    distance_from_last_txn_km: Optional[float] = None


class TransactionCreate(TransactionBase):
    """Payload schema for submitting a transaction."""
    user_id: str = Field(..., description="ID of purchasing/sending user")
    device_id: Optional[str] = Field(None, description="ID of source device")
    transaction_reference: Optional[str] = Field(None, max_length=64)
    timestamp: Optional[datetime] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class TransactionUpdate(BaseModel):
    """Payload schema for updating transaction status or risk disposition."""
    status: Optional[TransactionStatus] = None
    review_status: Optional[ReviewStatus] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    risk_level: Optional[RiskLevel] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class TransactionResponse(TransactionBase):
    """Response schema for transaction summary."""
    id: str
    transaction_reference: str
    user_id: str
    device_id: Optional[str] = None

    # Timestamps
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    # Risk assessment
    risk_score: float
    risk_level: RiskLevel
    status: TransactionStatus

    # Review status
    review_status: ReviewStatus

    extra_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionDetailResponse(TransactionResponse):
    """Comprehensive transaction response including triggered rules, flags, and reviews."""
    fraud_flags: List[FraudFlagResponse] = []
    rule_results: List[FraudRuleResultResponse] = []
    reviews: List[ReviewResponse] = []

    model_config = ConfigDict(from_attributes=True)

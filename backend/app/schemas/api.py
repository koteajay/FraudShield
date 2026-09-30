"""Pydantic schemas for Phase 9 Fraud APIs."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# 1. TRANSACTION INGESTION SCHEMAS
# ---------------------------------------------------------------------------

class TransactionIngestRequest(BaseModel):
    """Payload schema for submitting/ingesting a transaction."""

    user_id: str = Field(..., description="ID of purchasing/sending user")
    amount: float = Field(..., gt=0.0, description="Transaction monetary amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO currency code")
    merchant_id: Optional[str] = Field(None, description="Merchant identifier")
    merchant_name: Optional[str] = Field(None, description="Merchant business name")
    merchant_category: Optional[str] = Field(None, description="Merchant Category Code or industry")
    location: Optional[str] = Field(None, description="Descriptive location string")
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, max_length=3, description="Country code (ISO)")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    timestamp: Optional[datetime] = Field(None, description="Transaction submission timestamp")
    device_id: Optional[str] = Field(None, description="Client device identifier")
    payment_method: Optional[str] = Field(default="credit_card", description="Payment method")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class DeviceInfo(BaseModel):
    """Client device telemetry state."""

    device_id: Optional[str] = None
    is_new: bool = False


class RiskInfo(BaseModel):
    """Calculated risk scoring output."""

    score: float
    level: str
    explanation: str


class TriggeredRuleInfo(BaseModel):
    """Evaluation record of a triggered fraud heuristic rule."""

    rule_id: str
    rule_name: str
    reason: str
    score_contribution: float
    evidence: Dict[str, Any] = Field(default_factory=dict)


class AccountTakeoverInfo(BaseModel):
    """Compound account takeover evaluation output."""

    is_at_risk: bool
    risk_level: str
    signal_count: int
    signals: Dict[str, bool] = Field(default_factory=dict)
    explanation: str


class TransactionIngestResponse(BaseModel):
    """Comprehensive explainable response returned upon transaction ingestion."""

    id: str
    transaction_reference: str
    user_id: str
    amount: float
    currency: str
    merchant_name: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    device: DeviceInfo
    risk: RiskInfo
    triggered_rules: List[TriggeredRuleInfo] = Field(default_factory=list)
    account_takeover: Optional[AccountTakeoverInfo] = None
    status: str
    review_status: str


# ---------------------------------------------------------------------------
# 2. PAGINATED TRANSACTIONS & REVIEW SCHEMAS
# ---------------------------------------------------------------------------

class PaginatedTransactionsResponse(BaseModel):
    """Standardized pagination response for transactions."""

    items: List[Dict[str, Any]]
    page: int
    page_size: int
    total: int
    total_pages: int


class ReviewStatusUpdateRequest(BaseModel):
    """Payload schema for updating a transaction's review status."""

    status: str = Field(..., description="Target status: PENDING_REVIEW, REVIEWED, CLEARED, ESCALATED, etc.")


class ReviewStatusUpdateResponse(BaseModel):
    """Response returned upon updating review status."""

    id: str
    transaction_reference: str
    previous_review_status: str
    review_status: str
    updated_at: datetime


# ---------------------------------------------------------------------------
# 3. DASHBOARD & ANALYTICS SCHEMAS
# ---------------------------------------------------------------------------

class DashboardStatsResponse(BaseModel):
    """High-level KPIs and volume metrics for reviewer dashboard."""

    total_transactions: int
    pending_review: int
    high_risk_transactions: int
    critical_risk_transactions: int
    cleared_transactions: int
    reviewed_transactions: int
    average_risk_score: float
    new_devices: int
    account_takeover_risk_events: int


class RuleTriggerDistributionItem(BaseModel):
    """Count of occurrences for an individual triggered rule."""

    rule_id: str
    rule_name: str
    trigger_count: int


class DailyActivityItem(BaseModel):
    """Daily transaction volume and flagged transaction counts."""

    date: str
    transactions: int
    flagged: int


class FraudAnalyticsResponse(BaseModel):
    """Analytical distribution metrics for fraud reviewer reporting."""

    risk_distribution: Dict[str, int]
    rule_trigger_distribution: List[RuleTriggerDistributionItem]
    fraud_status_distribution: Dict[str, int]
    daily_activity: List[DailyActivityItem]


# ---------------------------------------------------------------------------
# 4. RULES & RULE PERFORMANCE SCHEMAS
# ---------------------------------------------------------------------------

class RuleItem(BaseModel):
    """Metadata schema for a registered fraud rule."""

    rule_id: str
    name: str
    description: str
    enabled: bool = True
    score_contribution: float


class RulesListResponse(BaseModel):
    """Response containing all registered active fraud rules."""

    rules: List[RuleItem]


class RulePerformanceItem(BaseModel):
    """Historical execution performance metrics for a fraud rule."""

    rule_id: str
    rule_name: str
    trigger_count: int
    evaluation_count: int
    trigger_rate: float
    total_score_contribution: float


class RulePerformanceResponse(BaseModel):
    """Performance statistics across all fraud rules."""

    rules: List[RulePerformanceItem]

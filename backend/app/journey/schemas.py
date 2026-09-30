"""Transaction Journey Pydantic Schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JourneyEventType(str, Enum):
    """Supported event categories in the chronological journey timeline."""

    TRANSACTION = "TRANSACTION"
    LOGIN_ATTEMPT = "LOGIN_ATTEMPT"
    DEVICE_EVENT = "DEVICE_EVENT"
    RISK_EVENT = "RISK_EVENT"
    RULE_TRIGGER = "RULE_TRIGGER"


class JourneySeverity(str, Enum):
    """Standardized visual and impact severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class JourneyEvent(BaseModel):
    """
    Normalized representation for an individual timeline event in a transaction journey.
    """

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type category (TRANSACTION, LOGIN_ATTEMPT, DEVICE_EVENT, RISK_EVENT, RULE_TRIGGER)")
    timestamp: datetime = Field(..., description="Chronological timestamp of the event")
    transaction_id: Optional[str] = Field(None, description="Associated transaction ID if applicable")
    user_id: str = Field(..., description="Owner or subject user identifier")
    title: str = Field(..., description="Human-friendly headline summary")
    description: str = Field(..., description="Detailed contextual narrative of the occurrence")
    location: Optional[str] = Field(None, description="Location context (city, country, or IP)")
    device_id: Optional[str] = Field(None, description="Originating client device identifier")
    amount: Optional[float] = Field(None, description="Monetary transfer value if transaction")
    currency: Optional[str] = Field(None, description="ISO currency code (e.g. INR, USD)")
    risk_score: Optional[float] = Field(None, description="Associated risk score [0-100]")
    risk_level: Optional[str] = Field(None, description="Associated risk level tier")
    rule_id: Optional[str] = Field(None, description="Associated fraud rule ID if rule trigger")
    severity: str = Field(default="INFO", description="Visual and operational severity rating")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Extensible telemetry, evidence, and attributes")


class JourneyWindow(BaseModel):
    """Start and end bounds of the chronological investigation window."""

    start: datetime = Field(..., description="Lower bound timestamp of journey window")
    end: datetime = Field(..., description="Upper bound timestamp of journey window")


class JourneySummary(BaseModel):
    """Aggregate statistics and high-level markers for the journey period."""

    transaction_count: int = Field(default=0, description="Total transactions within the window")
    login_attempt_count: int = Field(default=0, description="Total login attempts within the window")
    rule_trigger_count: int = Field(default=0, description="Total fraud rule triggers within the window")
    risk_event_count: int = Field(default=0, description="Total elevated risk and alert events")
    new_device_detected: bool = Field(default=False, description="Whether any unrecognized device was observed")
    locations: List[str] = Field(default_factory=list, description="Unique locations encountered chronologically")
    devices: List[str] = Field(default_factory=list, description="Unique devices encountered chronologically")


class TransactionJourneyResponse(BaseModel):
    """
    Complete chronological timeline response for a selected transaction.
    """

    transaction_id: str = Field(..., description="Subject transaction ID")
    user_id: str = Field(..., description="Subject user identifier")
    window: JourneyWindow = Field(..., description="Active time window surrounding the transaction")
    events: List[JourneyEvent] = Field(default_factory=list, description="Chronologically sorted timeline events")
    summary: JourneySummary = Field(..., description="Statistical summary of the journey window")

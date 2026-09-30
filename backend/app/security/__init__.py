"""Security module providing Account Takeover (ATO) correlation and detection."""

from app.security.models import (
    SignalStatus,
    AccountTakeoverSignals,
    AccountTakeoverAssessment,
)
from app.security.account_takeover import (
    AccountTakeoverDetector,
    SIGNAL_NEW_DEVICE,
    SIGNAL_NEW_LOCATION,
    SIGNAL_UNUSUAL_TIME,
    SIGNAL_FAILED_LOGIN,
    SIGNAL_UNUSUAL_TRANSACTION,
    SIGNAL_LABELS,
)
from app.security.schemas import AccountTakeoverResponse

__all__ = [
    "SignalStatus",
    "AccountTakeoverSignals",
    "AccountTakeoverAssessment",
    "AccountTakeoverDetector",
    "AccountTakeoverResponse",
    "SIGNAL_NEW_DEVICE",
    "SIGNAL_NEW_LOCATION",
    "SIGNAL_UNUSUAL_TIME",
    "SIGNAL_FAILED_LOGIN",
    "SIGNAL_UNUSUAL_TRANSACTION",
    "SIGNAL_LABELS",
]

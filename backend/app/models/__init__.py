"""Database Models and Enums package for FraudShield."""

from app.models.enums import (
    UserRole,
    RiskLevel,
    TransactionStatus,
    ReviewStatus,
    ReviewState,
    ReviewDecision,
    ReviewPriority,
    FlagSeverity,
    NotificationType,
    NotificationSeverity,
    NotificationChannel,
)
from app.models.user import User
from app.models.device import Device
from app.models.transaction import Transaction
from app.models.fraud_flag import FraudFlag
from app.models.fraud_rule_result import FraudRuleResult
from app.models.review import Review
from app.models.notification import Notification
from app.models.login_attempt import LoginAttempt

__all__ = [
    # Enums
    "UserRole",
    "RiskLevel",
    "TransactionStatus",
    "ReviewStatus",
    "ReviewState",
    "ReviewDecision",
    "ReviewPriority",
    "FlagSeverity",
    "NotificationType",
    "NotificationSeverity",
    "NotificationChannel",
    # Models
    "User",
    "Device",
    "Transaction",
    "FraudFlag",
    "FraudRuleResult",
    "Review",
    "Notification",
    "LoginAttempt",
]

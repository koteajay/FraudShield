"""Database Enumerations for FraudShield Core Models."""

from enum import Enum


class UserRole(str, Enum):
    """User access control role."""
    USER = "user"
    ANALYST = "analyst"
    ADMIN = "admin"


class RiskLevel(str, Enum):
    """Normalized risk categorization."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransactionStatus(str, Enum):
    """Processing and disposition state of a transaction."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    FLAGGED = "FLAGGED"
    UNDER_REVIEW = "UNDER_REVIEW"


class ReviewStatus(str, Enum):
    """Review lifecycle status of a transaction."""
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"
    CLEARED = "CLEARED"
    RESOLVED_LEGITIMATE = "RESOLVED_LEGITIMATE"
    RESOLVED_FRAUD = "RESOLVED_FRAUD"
    ESCALATED = "ESCALATED"


class ReviewState(str, Enum):
    """Investigation assignment state of a review case."""
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class ReviewDecision(str, Enum):
    """Final decision reached by the analyst."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_VERIFICATION = "REQUEST_VERIFICATION"
    ADD_TO_BLOCKLIST = "ADD_TO_BLOCKLIST"
    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"


class ReviewPriority(str, Enum):
    """Priority level for analyst review queue."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class FlagSeverity(str, Enum):
    """Severity classification of fraud flags and rules."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationType(str, Enum):
    """Categorization of notification events."""
    SUSPICIOUS_TRANSACTION = "SUSPICIOUS_TRANSACTION"
    NEW_DEVICE_LOGIN = "NEW_DEVICE_LOGIN"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    FRAUD_ALERT = "FRAUD_ALERT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class NotificationSeverity(str, Enum):
    """Severity of a user or analyst notification."""
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationChannel(str, Enum):
    """Delivery channel for notifications."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"

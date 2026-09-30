"""Pydantic schemas package for FraudShield."""

from app.schemas.enums import (
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
from app.schemas.user import UserBase, UserCreate, UserUpdate, UserResponse
from app.schemas.device import DeviceBase, DeviceCreate, DeviceResponse
from app.schemas.fraud_flag import FraudFlagBase, FraudFlagCreate, FraudFlagResponse
from app.schemas.fraud_rule_result import (
    FraudRuleResultBase,
    FraudRuleResultCreate,
    FraudRuleResultResponse,
)
from app.schemas.review import (
    ReviewBase,
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
)
from app.schemas.login_attempt import (
    LoginAttemptBase,
    LoginAttemptCreate,
    LoginAttemptResponse,
)
from app.schemas.transaction import (
    LocationData,
    MerchantData,
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionDetailResponse,
)

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
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    # Device
    "DeviceBase",
    "DeviceCreate",
    "DeviceResponse",
    # FraudFlag
    "FraudFlagBase",
    "FraudFlagCreate",
    "FraudFlagResponse",
    # FraudRuleResult
    "FraudRuleResultBase",
    "FraudRuleResultCreate",
    "FraudRuleResultResponse",
    # Review
    "ReviewBase",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    # Notification
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    # LoginAttempt
    "LoginAttemptBase",
    "LoginAttemptCreate",
    "LoginAttemptResponse",
    # Transaction
    "LocationData",
    "MerchantData",
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "TransactionDetailResponse",
]

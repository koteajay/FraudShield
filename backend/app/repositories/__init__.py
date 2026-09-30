"""Repositories package for FraudShield persistence layer."""

from app.repositories.base import BaseRepository
from app.repositories.user_repo import (
    UserRepository,
    DeviceRepository,
    LoginAttemptRepository,
)
from app.repositories.transaction_repo import (
    TransactionRepository,
    FraudFlagRepository,
    FraudRuleResultRepository,
    ReviewRepository,
)
from app.repositories.notification_repo import NotificationRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "DeviceRepository",
    "LoginAttemptRepository",
    "TransactionRepository",
    "FraudFlagRepository",
    "FraudRuleResultRepository",
    "ReviewRepository",
    "NotificationRepository",
]

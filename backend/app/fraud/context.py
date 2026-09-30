"""RuleContext container providing data required for fraud rule evaluation."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.config import get_settings


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract an attribute or dictionary key safely."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class RuleContext:
    """
    Decoupled context object encapsulating all domain data needed by fraud rules.
    Prevents rules from issuing ad-hoc database queries or binding to HTTP requests.
    """

    def __init__(
        self,
        current_transaction: Any,
        user: Optional[Any] = None,
        recent_transactions: Optional[List[Any]] = None,
        historical_transactions: Optional[List[Any]] = None,
        known_devices: Optional[List[Any]] = None,
        current_device: Optional[Any] = None,
        login_attempts: Optional[List[Any]] = None,
        user_profile: Optional[Any] = None,
        config: Optional[Any] = None,
        custom_parameters: Optional[Dict[str, Any]] = None,
    ):
        self.current_transaction = current_transaction
        self.user = user
        self.recent_transactions = list(recent_transactions or [])
        self.historical_transactions = list(historical_transactions or [])
        self.known_devices = list(known_devices or [])
        self.current_device = current_device
        self.login_attempts = list(login_attempts or [])
        self.user_profile = user_profile
        self.config = config or get_settings()
        self.custom_parameters = dict(custom_parameters or {})

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Retrieve configuration threshold.
        Prioritizes custom_parameters over application settings.
        """
        if key in self.custom_parameters:
            return self.custom_parameters[key]
        if hasattr(self.config, key):
            return getattr(self.config, key)
        if isinstance(self.config, dict) and key in self.config:
            return self.config[key]
        return default

    def get_transaction_field(self, field_name: str, default: Any = None) -> Any:
        """Safely retrieve a field from current_transaction."""
        return _safe_get(self.current_transaction, field_name, default)

    def get_transaction_timestamp(self) -> datetime:
        """Retrieve timestamp of current transaction (defaults to now)."""
        ts = self.get_transaction_field("timestamp")
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.now(timezone.utc)

    def get_transaction_amount(self) -> float:
        """Retrieve monetary amount of current transaction."""
        amt = self.get_transaction_field("amount", 0.0)
        try:
            return float(amt)
        except (ValueError, TypeError):
            return 0.0

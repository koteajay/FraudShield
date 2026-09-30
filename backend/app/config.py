"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    APP_NAME: str = "FraudShield"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./fraudshield.db"
    API_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Phase 3: Fraud Rule Engine Settings
    VELOCITY_THRESHOLD_COUNT: int = 5
    VELOCITY_WINDOW_MINUTES: int = 5

    UNUSUAL_AMOUNT_MULTIPLIER: float = 3.0
    UNUSUAL_AMOUNT_MIN_HISTORY: int = 3
    UNUSUAL_AMOUNT_MIN_THRESHOLD: float = 100.0

    IMPOSSIBLE_TRAVEL_MAX_SPEED_KMH: float = 900.0

    UNUSUAL_TIME_MIN_HISTORY: int = 5
    UNUSUAL_TIME_BUFFER_HOURS: int = 1

    FAILED_LOGIN_THRESHOLD: int = 3
    FAILED_LOGIN_WINDOW_MINUTES: int = 10

    UNUSUAL_MERCHANT_MIN_HISTORY: int = 3

    BLACKLISTED_COUNTRIES: List[str] = [
        "PRK",
        "IRN",
        "SYR",
        "CUB",
        "RUS",
    ]

    # Phase 4: Risk Scoring & Threshold Settings
    RISK_LOW_MAX: float = 29.0
    RISK_MEDIUM_MAX: float = 59.0
    RISK_HIGH_MAX: float = 79.0

    # Rule Score Contributions (Configurable Weights)
    SCORE_TRANSACTION_VELOCITY: float = 25.0
    SCORE_UNUSUAL_TRANSACTION_AMOUNT: float = 30.0
    SCORE_IMPOSSIBLE_GEOGRAPHICAL_LOCATION: float = 35.0
    SCORE_DEVICE_CHANGE: float = 15.0
    SCORE_UNUSUAL_TIME: float = 10.0
    SCORE_MULTIPLE_FAILED_LOGIN: float = 20.0
    SCORE_UNUSUAL_MERCHANT: float = 15.0
    SCORE_BLACKLISTED_COUNTRY: float = 30.0

    # Phase 5: User Behaviour Profile Settings
    BEHAVIOUR_PROFILE_DAYS: int = 30
    PROFILE_INSUFFICIENT_THRESHOLD: int = 5
    PROFILE_DEVELOPING_THRESHOLD: int = 20
    PROFILE_AMOUNT_RANGE_MULTIPLIER: float = 1.5
    PROFILE_LOCATION_MIN_COUNT: int = 1

    # Phase 7: Account Takeover Detection Settings
    ATO_MEDIUM_SIGNAL_COUNT: int = 2
    ATO_HIGH_SIGNAL_COUNT: int = 3
    ATO_CRITICAL_SIGNAL_COUNT: int = 4
    ATO_FAILED_LOGIN_WINDOW_MINUTES: int = 30
    ATO_FAILED_LOGIN_THRESHOLD: int = 3

    # Phase 8: Transaction Journey Settings
    JOURNEY_BEFORE_MINUTES: int = 30
    JOURNEY_AFTER_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("BLACKLISTED_COUNTRIES", mode="before")
    @classmethod
    def assemble_blacklisted_countries(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [c.upper().strip() for c in parsed]
            except Exception:
                return [country.upper().strip() for country in v.split(",") if country.strip()]
        elif isinstance(v, list):
            return [str(c).upper().strip() for c in v]
        return v

    def validate_risk_thresholds(self) -> None:
        """Validate that risk thresholds form a strictly ascending valid range."""
        if not (0.0 <= self.RISK_LOW_MAX < self.RISK_MEDIUM_MAX < self.RISK_HIGH_MAX <= 100.0):
            raise ValueError(
                f"Invalid risk thresholds: 0 <= {self.RISK_LOW_MAX} < "
                f"{self.RISK_MEDIUM_MAX} < {self.RISK_HIGH_MAX} <= 100 constraint violated"
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_risk_thresholds()
    return settings



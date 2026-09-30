"""Fraud Rules package exposing all standard rules and registry factory."""

from typing import List
from app.fraud.base import FraudRule
from app.fraud.rules.velocity import TransactionVelocityRule
from app.fraud.rules.unusual_amount import UnusualTransactionAmountRule
from app.fraud.rules.impossible_location import ImpossibleGeographicalLocationRule
from app.fraud.rules.device_change import DeviceChangeRule
from app.fraud.rules.unusual_time import UnusualTimeRule
from app.fraud.rules.failed_login import MultipleFailedLoginRule
from app.fraud.rules.unusual_merchant import UnusualMerchantRule
from app.fraud.rules.blacklisted_country import BlacklistedCountryRule

__all__ = [
    "TransactionVelocityRule",
    "UnusualTransactionAmountRule",
    "ImpossibleGeographicalLocationRule",
    "DeviceChangeRule",
    "UnusualTimeRule",
    "MultipleFailedLoginRule",
    "UnusualMerchantRule",
    "BlacklistedCountryRule",
    "get_default_rules",
]


def get_default_rules() -> List[FraudRule]:
    """Instantiate and return the suite of 8 core fraud rules."""
    return [
        TransactionVelocityRule(),
        UnusualTransactionAmountRule(),
        ImpossibleGeographicalLocationRule(),
        DeviceChangeRule(),
        UnusualTimeRule(),
        MultipleFailedLoginRule(),
        UnusualMerchantRule(),
        BlacklistedCountryRule(),
    ]

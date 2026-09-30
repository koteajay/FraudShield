"""Blacklisted Country Fraud Rule."""

from typing import List, Set
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext
from app.fraud.result import RuleResult


class BlacklistedCountryRule(FraudRule):
    """
    Detects transactions associated with configured high-risk or blocked countries.
    Note: The blacklist is an application configuration for demo/policy compliance,
    not an authoritative political classification.
    """

    @property
    def rule_id(self) -> str:
        return "blacklisted_country"

    @property
    def name(self) -> str:
        return "Blacklisted Country"

    @property
    def description(self) -> str:
        return "Flags transactions originating or terminating in configured restricted jurisdictions."

    @property
    def default_score_contribution(self) -> float:
        return 30.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        raw_blacklist = context.get_config_value("BLACKLISTED_COUNTRIES", ["PRK", "IRN", "SYR", "CUB", "RUS"])
        if isinstance(raw_blacklist, str):
            blacklist = {c.strip().upper() for c in raw_blacklist.split(",") if c.strip()}
        elif isinstance(raw_blacklist, (list, set, tuple)):
            blacklist = {str(c).strip().upper() for c in raw_blacklist if str(c).strip()}
        else:
            blacklist = set()

        # Check all country fields present on transaction
        curr_country = context.get_transaction_field("country")
        billing_country = context.get_transaction_field("billing_country")
        shipping_country = context.get_transaction_field("shipping_country")

        evaluated_countries: Set[str] = set()
        matched_countries: List[str] = []

        for c in (curr_country, billing_country, shipping_country):
            if c:
                code = str(c).strip().upper()
                evaluated_countries.add(code)
                if code in blacklist and code not in matched_countries:
                    matched_countries.append(code)

        if not evaluated_countries:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="No country geographic information provided on transaction.",
                evidence={"status": "missing_country_data"},
                score_contribution=0.0,
            )

        triggered = len(matched_countries) > 0
        if triggered:
            reason = (
                f"Transaction is associated with restricted country code(s) "
                f"({', '.join(matched_countries)}) present in the configured application blacklist."
            )
            score = self.default_score_contribution
        else:
            reason = "Transaction country does not match the configured application blacklist."
            score = 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "transaction_country": curr_country,
                "billing_country": billing_country,
                "shipping_country": shipping_country,
                "matched": triggered,
                "matched_countries": matched_countries,
                "configured_blacklist": sorted(list(blacklist)),
            },
            score_contribution=score,
        )

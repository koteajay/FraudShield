"""Unusual Merchant Fraud Rule."""

from typing import Set
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


class UnusualMerchantRule(FraudRule):
    """
    Detects transactions involving merchants or merchant categories that diverge
    from the user's historical transaction behavior.
    """

    @property
    def rule_id(self) -> str:
        return "unusual_merchant"

    @property
    def name(self) -> str:
        return "Unusual Merchant"

    @property
    def description(self) -> str:
        return "Flags transactions involving merchant categories completely unseen in user history."

    @property
    def default_score_contribution(self) -> float:
        return 15.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        min_history = int(context.get_config_value("UNUSUAL_MERCHANT_MIN_HISTORY", 3))

        curr_category = context.get_transaction_field("merchant_category")
        curr_merchant_id = context.get_transaction_field("merchant_id")
        curr_merchant_name = context.get_transaction_field("merchant_name")
        curr_id = context.get_transaction_field("id")

        if not curr_category and not curr_merchant_id and not curr_merchant_name:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="No merchant identifier or category provided for this transaction.",
                evidence={"status": "missing_merchant_telemetry"},
                score_contribution=0.0,
            )

        # If user_profile is provided in RuleContext, use it
        profile = getattr(context, "user_profile", None)
        if profile is not None:
            sample_size = getattr(profile, "profile_transaction_count", 0)
            if sample_size < min_history:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    triggered=False,
                    reason="Insufficient historical transactions with merchant data to establish baseline.",
                    evidence={
                        "historical_merchant_count": sample_size,
                        "required_minimum": min_history,
                    },
                    score_contribution=0.0,
                )

            profile_known_categories = {c.lower() for c in getattr(profile, "known_categories", [])}
            profile_known_merchants = set()
            for m in getattr(profile, "known_merchants", []):
                mid = getattr(m, "merchant_id", None)
                mname = getattr(m, "merchant_name", None)
                if mid:
                    profile_known_merchants.add(mid.strip().lower())
                if mname:
                    profile_known_merchants.add(mname.strip().lower())

            triggered = False
            reason = ""
            is_new_category = False

            if curr_category:
                normalized_curr = curr_category.strip().lower()
                if normalized_curr not in profile_known_categories:
                    triggered = True
                    is_new_category = True
                    reason = (
                        f"Merchant category '{curr_category}' has never been frequented by this user."
                    )
                else:
                    reason = f"Merchant category '{curr_category}' matches established user profile."
            else:
                m_key = (curr_merchant_id or curr_merchant_name or "").strip().lower()
                if m_key not in profile_known_merchants:
                    triggered = True
                    reason = f"Merchant '{curr_merchant_name or curr_merchant_id}' is previously unseen for this user."
                else:
                    reason = f"Merchant '{curr_merchant_name or curr_merchant_id}' is a recognized merchant."

            score = self.default_score_contribution if triggered else 0.0

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=triggered,
                reason=reason,
                evidence={
                    "current_merchant": curr_merchant_name or curr_merchant_id,
                    "current_category": curr_category,
                    "known_categories": sorted(list(profile_known_categories)),
                    "is_new_category": is_new_category,
                    "historical_merchant_sample_size": sample_size,
                },
                score_contribution=score,
            )

        # Collect historical merchant profile info
        known_categories: Set[str] = set()
        known_merchants: Set[str] = set()
        historical_merchant_txns = 0

        for txn in context.historical_transactions:
            txn_id = _safe_get(txn, "id")
            if txn_id and curr_id and txn_id == curr_id:
                continue
            cat = _safe_get(txn, "merchant_category")
            mid = _safe_get(txn, "merchant_id")
            mname = _safe_get(txn, "merchant_name")

            if cat or mid or mname:
                historical_merchant_txns += 1
            if cat:
                known_categories.add(cat.strip().lower())
            if mid:
                known_merchants.add(mid.strip().lower())
            if mname:
                known_merchants.add(mname.strip().lower())

        if historical_merchant_txns < min_history:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="Insufficient historical transactions with merchant data to establish baseline.",
                evidence={
                    "historical_merchant_count": historical_merchant_txns,
                    "required_minimum": min_history,
                },
                score_contribution=0.0,
            )

        triggered = False
        reason = ""
        is_new_category = False

        if curr_category:
            normalized_curr = curr_category.strip().lower()
            if normalized_curr not in known_categories:
                triggered = True
                is_new_category = True
                reason = (
                    f"Merchant category '{curr_category}' has never been frequented by this user."
                )
            else:
                reason = f"Merchant category '{curr_category}' matches established user profile."
        else:
            # Fall back to merchant identifier matching
            m_key = (curr_merchant_id or curr_merchant_name or "").strip().lower()
            if m_key not in known_merchants:
                triggered = True
                reason = f"Merchant '{curr_merchant_name or curr_merchant_id}' is previously unseen for this user."
            else:
                reason = f"Merchant '{curr_merchant_name or curr_merchant_id}' is a recognized merchant."

        score = self.default_score_contribution if triggered else 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "current_merchant": curr_merchant_name or curr_merchant_id,
                "current_category": curr_category,
                "known_categories": sorted(list(known_categories)),
                "is_new_category": is_new_category,
                "historical_merchant_sample_size": historical_merchant_txns,
            },
            score_contribution=score,
        )

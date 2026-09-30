"""Unusual Transaction Amount Fraud Rule."""

from typing import List
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


class UnusualTransactionAmountRule(FraudRule):
    """
    Detects transactions significantly larger than the user's historical average spend.
    Provides explainable ratio comparisons.
    """

    @property
    def rule_id(self) -> str:
        return "unusual_transaction_amount"

    @property
    def name(self) -> str:
        return "Unusual Transaction Amount"

    @property
    def description(self) -> str:
        return "Flags transactions that deviate significantly from a user's average spending pattern."

    @property
    def default_score_contribution(self) -> float:
        return 30.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        multiplier = float(context.get_config_value("UNUSUAL_AMOUNT_MULTIPLIER", 3.0))
        min_history = int(context.get_config_value("UNUSUAL_AMOUNT_MIN_HISTORY", 3))
        min_threshold = float(context.get_config_value("UNUSUAL_AMOUNT_MIN_THRESHOLD", 100.0))

        current_amount = context.get_transaction_amount()
        current_id = context.get_transaction_field("id")

        # Check if pre-computed UserBehaviourProfile is present in context
        prof = getattr(context, "user_profile", None)
        if prof and hasattr(prof, "average_transaction_amount") and prof.average_transaction_amount is not None:
            sample_size = getattr(prof, "profile_transaction_count", min_history)
            if sample_size < min_history:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    triggered=False,
                    reason="Insufficient historical transactions to establish an amount baseline.",
                    evidence={
                        "current_amount": round(current_amount, 2),
                        "historical_count": sample_size,
                        "required_minimum": min_history,
                    },
                    score_contribution=0.0,
                )
            historical_average = float(prof.average_transaction_amount)
            historical_count = sample_size
        else:
            # Collect past transaction amounts (exclude current transaction if present)
            historical_amounts: List[float] = []
            for txn in context.historical_transactions:
                txn_id = _safe_get(txn, "id")
                if txn_id and current_id and txn_id == current_id:
                    continue
                amt = _safe_get(txn, "amount")
                if amt is not None:
                    try:
                        val = float(amt)
                        if val > 0:
                            historical_amounts.append(val)
                    except (ValueError, TypeError):
                        continue

            if len(historical_amounts) < min_history:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    triggered=False,
                    reason="Insufficient historical transactions to establish an amount baseline.",
                    evidence={
                        "current_amount": round(current_amount, 2),
                        "historical_count": len(historical_amounts),
                        "required_minimum": min_history,
                    },
                    score_contribution=0.0,
                )
            historical_average = sum(historical_amounts) / len(historical_amounts)
            historical_count = len(historical_amounts)

        comparison_ratio = current_amount / historical_average if historical_average > 0 else 0.0

        triggered = (
            current_amount > (historical_average * multiplier)
            and current_amount >= min_threshold
        )

        if triggered:
            reason = (
                f"Transaction amount ({current_amount:.2f}) exceeds {multiplier}x "
                f"the historical average ({historical_average:.2f}) by a factor of {comparison_ratio:.2f}."
            )
            score = self.default_score_contribution
        else:
            reason = (
                f"Transaction amount ({current_amount:.2f}) is within expected baseline "
                f"(average: {historical_average:.2f}, multiplier: {multiplier}x)."
            )
            score = 0.0

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "current_amount": round(current_amount, 2),
                "historical_average": round(historical_average, 2),
                "multiplier": multiplier,
                "comparison_ratio": round(comparison_ratio, 2),
                "historical_sample_size": historical_count,
            },
            score_contribution=score,
        )

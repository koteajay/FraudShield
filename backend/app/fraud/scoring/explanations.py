"""Deterministic Human-Readable Explanation Generator for Risk Assessments."""

from typing import List
from app.models.enums import RiskLevel
from app.fraud.scoring.models import RuleContribution


def _format_score(score: float) -> str:
    """Format numeric score cleanly as integer or 1-decimal float."""
    if float(score).is_integer():
        return str(int(score))
    return f"{score:.1f}"


def generate_explanation(
    final_score: float,
    risk_level: RiskLevel,
    triggered_contributions: List[RuleContribution],
) -> str:
    """
    Generate a deterministic, transparent explanation for a transaction's risk assessment.
    Does NOT use AI or LLMs.
    Grounds explanation strictly in verified rule triggers and evidence without asserting certainty of fraud.
    """
    score_str = _format_score(final_score)
    count = len(triggered_contributions)

    if count == 0:
        return (
            "No suspicious rule conditions were triggered for this transaction. "
            f"The transaction currently has a {risk_level.value.lower()} risk score of {score_str}."
        )

    if count == 1:
        contrib = triggered_contributions[0]
        # Clean up reason if ending with period
        clean_reason = contrib.reason.rstrip(".")
        return (
            f"Transaction classified as {risk_level.value} risk with a score of {score_str}. "
            f"The {contrib.rule_name} rule was triggered: {clean_reason}."
        )

    # Multiple rules triggered: list contributions clearly
    formatted_items = [
        f"{c.rule_name} (+{_format_score(c.score)})"
        for c in triggered_contributions
    ]

    if len(formatted_items) == 2:
        patterns_text = f"{formatted_items[0]} and {formatted_items[1]}"
    else:
        patterns_text = f"{', '.join(formatted_items[:-1])}, and {formatted_items[-1]}"

    return (
        f"Transaction classified as {risk_level.value} risk with a score of {score_str}. "
        f"The following {count} suspicious patterns were detected: {patterns_text}."
    )

"""Impossible Geographical Location Fraud Rule."""

import math
from datetime import datetime, timezone
from typing import Any, Optional, Tuple
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two geographic points
    using the Haversine formula on a spherical Earth (R = 6371.0 km).
    """
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _parse_ts(ts: Any) -> datetime:
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass
    return datetime.now(timezone.utc)


class ImpossibleGeographicalLocationRule(FraudRule):
    """
    Detects impossible travel speed between consecutive transaction locations
    using great-circle Haversine distance and elapsed timestamps.
    """

    @property
    def rule_id(self) -> str:
        return "impossible_geographical_location"

    @property
    def name(self) -> str:
        return "Impossible Geographical Location"

    @property
    def description(self) -> str:
        return "Flags transactions that require superhuman travel velocity between consecutive physical locations."

    @property
    def default_score_contribution(self) -> float:
        return 35.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        max_speed_kmh = float(context.get_config_value("IMPOSSIBLE_TRAVEL_MAX_SPEED_KMH", 900.0))

        curr_lat = context.get_transaction_field("latitude")
        curr_lon = context.get_transaction_field("longitude")
        curr_time = _parse_ts(context.get_transaction_timestamp())
        curr_id = context.get_transaction_field("id")

        if curr_lat is None or curr_lon is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="Current transaction does not provide geographic coordinates.",
                evidence={"status": "missing_current_coordinates"},
                score_contribution=0.0,
            )

        try:
            lat2, lon2 = float(curr_lat), float(curr_lon)
        except (ValueError, TypeError):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="Invalid geographic coordinate format on current transaction.",
                evidence={"status": "invalid_coordinates"},
                score_contribution=0.0,
            )

        # Find the most recent prior transaction with valid coordinates
        prior_txn = None
        prior_time = None
        prior_lat, prior_lon = None, None

        # Pool transactions from recent and historical lists
        candidate_txns = list(context.recent_transactions) + list(context.historical_transactions)

        # Sort candidate transactions descending by timestamp
        dated_candidates = []
        for txn in candidate_txns:
            txn_id = _safe_get(txn, "id")
            if txn_id and curr_id and txn_id == curr_id:
                continue
            t_time = _parse_ts(_safe_get(txn, "timestamp"))
            if t_time <= curr_time:
                t_lat = _safe_get(txn, "latitude")
                t_lon = _safe_get(txn, "longitude")
                if t_lat is not None and t_lon is not None:
                    try:
                        dated_candidates.append((t_time, float(t_lat), float(t_lon), txn))
                    except (ValueError, TypeError):
                        continue

        if not dated_candidates:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="No prior transaction with geographic coordinates found for comparison.",
                evidence={"status": "no_prior_coordinates"},
                score_contribution=0.0,
            )

        dated_candidates.sort(key=lambda x: x[0], reverse=True)
        prior_time, prior_lat, prior_lon, prior_txn = dated_candidates[0]

        # Calculate distance and elapsed time
        distance_km = haversine_distance_km(prior_lat, prior_lon, lat2, lon2)
        elapsed_seconds = (curr_time - prior_time).total_seconds()
        elapsed_hours = elapsed_seconds / 3600.0

        if distance_km < 1.0:
            # Same immediate location
            required_speed = 0.0
            triggered = False
            reason = "Transactions occurred in the same vicinity."
            score = 0.0
        elif elapsed_hours <= (1.0 / 3600.0):  # Less than 1 second apart
            # Physically distinct location with near-zero time difference
            required_speed = distance_km / 0.001
            triggered = True
            reason = (
                f"Simultaneous transactions detected across {distance_km:.1f} km "
                f"with {elapsed_seconds:.0f}s elapsed time."
            )
            score = self.default_score_contribution
        else:
            required_speed = distance_km / elapsed_hours
            triggered = required_speed > max_speed_kmh
            if triggered:
                reason = (
                    f"Required travel speed of {required_speed:.1f} km/h between locations "
                    f"exceeds maximum realistic threshold ({max_speed_kmh:.1f} km/h)."
                )
                score = self.default_score_contribution
            else:
                reason = (
                    f"Travel speed between locations ({required_speed:.1f} km/h) "
                    f"is realistic (threshold: {max_speed_kmh:.1f} km/h)."
                )
                score = 0.0

        prev_city = _safe_get(prior_txn, "city")
        prev_country = _safe_get(prior_txn, "country")
        curr_city = context.get_transaction_field("city")
        curr_country = context.get_transaction_field("country")

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence={
                "previous_location": {
                    "latitude": prior_lat,
                    "longitude": prior_lon,
                    "city": prev_city,
                    "country": prev_country,
                },
                "current_location": {
                    "latitude": lat2,
                    "longitude": lon2,
                    "city": curr_city,
                    "country": curr_country,
                },
                "distance_km": round(distance_km, 2),
                "elapsed_minutes": round(elapsed_seconds / 60.0, 2),
                "required_speed_kmh": round(required_speed, 2),
                "max_speed_threshold_kmh": max_speed_kmh,
            },
            score_contribution=score,
        )

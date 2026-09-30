"""Deterministic User Behaviour Profile Calculator."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from app.behaviour.models import (
    AmountRange,
    BehaviourComparison,
    DeviceSummary,
    LocationSummary,
    MerchantSummary,
    ProfileStatus,
    TimeWindow,
    UserBehaviourProfile,
)


def _safe_get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _parse_datetime(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
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
            return None
    return None


class BehaviourProfileCalculator:
    """
    Pure mathematical and deterministic calculator for building user behavioural baselines.
    Zero machine learning, zero external APIs.
    """

    @staticmethod
    def calculate_amount_metrics(
        amounts: List[float],
        multiplier: float = 1.5,
    ) -> Tuple[
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[float],
        Optional[AmountRange],
    ]:
        """Calculate historical average, extremes, and normal expected amount boundaries."""
        valid_amounts = [float(a) for a in amounts if a is not None and float(a) >= 0.0]
        if not valid_amounts:
            return None, None, None, None, None, None

        avg = round(sum(valid_amounts) / len(valid_amounts), 2)
        min_amt = round(min(valid_amounts), 2)
        max_amt = round(max(valid_amounts), 2)

        # Lower bound: max of 0.0 or average scaled down
        lower_bound = max(0.0, round(min(min_amt, avg * 0.5), 2))
        # Upper bound: scaled by multiplier around average or historical max
        upper_bound = round(max(max_amt, avg * multiplier), 2)

        amount_range = AmountRange(min=lower_bound, max=upper_bound)
        return avg, min_amt, max_amt, lower_bound, upper_bound, amount_range

    @staticmethod
    def calculate_frequency_metrics(
        timestamps: List[datetime],
        period_days: int = 30,
    ) -> Tuple[float, int, int]:
        """Calculate daily velocity and distinct calendar days with transactions."""
        count = len(timestamps)
        if count == 0:
            return 0.0, 0, 0

        # Unique active calendar days
        unique_days: Set[str] = {
            ts.strftime("%Y-%m-%d") for ts in timestamps if ts is not None
        }
        active_days = len(unique_days)
        avg_per_day = round(count / max(1, period_days), 2)
        return avg_per_day, active_days, count

    @staticmethod
    def calculate_hours_metrics(
        timestamps: List[datetime],
    ) -> Tuple[Optional[int], Optional[int], Optional[TimeWindow]]:
        """Determine historical daily active transaction hour boundaries."""
        hours = [ts.hour for ts in timestamps if ts is not None]
        if not hours:
            return None, None, None

        start_h = min(hours)
        end_h = max(hours)
        time_window = TimeWindow(
            start=f"{start_h:02d}:00",
            end=f"{end_h:02d}:00",
            start_hour=start_h,
            end_hour=end_h,
        )
        return start_h, end_h, time_window

    @staticmethod
    def calculate_location_metrics(
        transactions: List[Any],
        min_count: int = 1,
    ) -> Tuple[List[str], List[LocationSummary]]:
        """Identify familiar geographic locations observed in historical activity."""
        loc_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for txn in transactions:
            city = _safe_get(txn, "city")
            country = _safe_get(txn, "country")
            lat = _safe_get(txn, "latitude")
            lon = _safe_get(txn, "longitude")

            if city or country:
                c_str = str(city).strip() if city else "Unknown"
                co_str = str(country).strip().upper() if country else ""
                key = (c_str.lower(), co_str.lower())

                if key not in loc_map:
                    loc_map[key] = {
                        "city": c_str,
                        "country": co_str,
                        "count": 0,
                        "latitude": float(lat) if lat is not None else None,
                        "longitude": float(lon) if lon is not None else None,
                    }
                loc_map[key]["count"] += 1

        detailed: List[LocationSummary] = []
        known_strings: List[str] = []

        # Sort by frequency descending
        sorted_locs = sorted(loc_map.values(), key=lambda x: x["count"], reverse=True)
        for item in sorted_locs:
            if item["count"] >= min_count:
                detailed.append(
                    LocationSummary(
                        city=item["city"],
                        country=item["country"],
                        transaction_count=item["count"],
                        latitude=item["latitude"],
                        longitude=item["longitude"],
                    )
                )
                label = f"{item['city']}, {item['country']}" if item["country"] else item["city"]
                if label not in known_strings:
                    known_strings.append(label)

        return known_strings, detailed

    @staticmethod
    def calculate_merchant_metrics(
        transactions: List[Any],
    ) -> Tuple[List[str], List[str], List[MerchantSummary]]:
        """Extract frequently visited merchants and familiar industry categories."""
        merchant_map: Dict[str, Dict[str, Any]] = {}
        known_categories: Set[str] = set()

        for txn in transactions:
            m_id = _safe_get(txn, "merchant_id")
            m_name = _safe_get(txn, "merchant_name")
            m_cat = _safe_get(txn, "merchant_category")

            if m_cat:
                known_categories.add(str(m_cat).strip())

            label = m_name or m_id
            if label:
                clean_label = str(label).strip()
                key = clean_label.lower()
                if key not in merchant_map:
                    merchant_map[key] = {
                        "merchant_id": str(m_id) if m_id else None,
                        "merchant_name": clean_label,
                        "merchant_category": str(m_cat) if m_cat else None,
                        "count": 0,
                    }
                merchant_map[key]["count"] += 1

        detailed = [
            MerchantSummary(
                merchant_id=v["merchant_id"],
                merchant_name=v["merchant_name"],
                merchant_category=v["merchant_category"],
                transaction_count=v["count"],
            )
            for v in sorted(merchant_map.values(), key=lambda x: x["count"], reverse=True)
        ]
        known_names = [v.merchant_name for v in detailed if v.merchant_name]
        return known_names, sorted(list(known_categories)), detailed

    @staticmethod
    def calculate_device_metrics(
        devices: List[Any],
        transactions: List[Any],
    ) -> Tuple[int, List[str], List[str], List[DeviceSummary]]:
        """Identify devices enrolled or historically used by the user."""
        seen_device_ids: Set[str] = set()
        seen_fingerprints: Set[str] = set()
        detailed: List[DeviceSummary] = []

        # From explicit Device records
        for d in devices:
            d_id = str(_safe_get(d, "id"))
            fp = _safe_get(d, "fingerprint")
            dtype = _safe_get(d, "device_type", "unknown")
            first_seen = _parse_datetime(_safe_get(d, "first_seen_at"))
            last_seen = _parse_datetime(_safe_get(d, "last_seen_at"))

            if d_id:
                seen_device_ids.add(d_id)
            if fp:
                seen_fingerprints.add(str(fp))

            detailed.append(
                DeviceSummary(
                    device_id=d_id,
                    fingerprint=str(fp) if fp else None,
                    device_type=str(dtype),
                    first_seen_at=first_seen,
                    last_seen_at=last_seen,
                )
            )

        # Also capture any device IDs from transaction history
        for txn in transactions:
            t_did = _safe_get(txn, "device_id")
            if t_did and str(t_did) not in seen_device_ids:
                seen_device_ids.add(str(t_did))
                detailed.append(
                    DeviceSummary(
                        device_id=str(t_did),
                        device_type="transaction_telemetry",
                    )
                )

        return (
            len(seen_device_ids) or len(seen_fingerprints),
            sorted(list(seen_device_ids)),
            sorted(list(seen_fingerprints)),
            detailed,
        )

    @staticmethod
    def calculate_login_metrics(
        login_attempts: List[Any],
        period_start: Optional[datetime] = None,
        recent_window_minutes: int = 15,
        now: Optional[datetime] = None,
    ) -> Tuple[int, int, Optional[datetime]]:
        """Tally failed logins across historical profile window and immediate recent window."""
        ref_time = now or datetime.now(timezone.utc)
        recent_cutoff = ref_time - timedelta(minutes=recent_window_minutes)

        total_failed = 0
        recent_failed = 0
        latest_failed: Optional[datetime] = None

        for attempt in login_attempts:
            is_success = bool(_safe_get(attempt, "is_successful", False))
            attempt_time = _parse_datetime(_safe_get(attempt, "timestamp"))

            if not is_success and attempt_time is not None:
                # Check within 30-day period
                if period_start is None or attempt_time >= period_start:
                    total_failed += 1

                # Check within recent 15-min window
                if attempt_time >= recent_cutoff:
                    recent_failed += 1

                # Latest timestamp
                if latest_failed is None or attempt_time > latest_failed:
                    latest_failed = attempt_time

        return total_failed, recent_failed, latest_failed

    @staticmethod
    def determine_profile_status(
        transaction_count: int,
        insufficient_threshold: int = 5,
        developing_threshold: int = 20,
    ) -> ProfileStatus:
        """Categorize data sufficiency: INSUFFICIENT_DATA (0-4), DEVELOPING (5-19), ESTABLISHED (20+)."""
        if transaction_count < insufficient_threshold:
            return ProfileStatus.INSUFFICIENT_DATA
        elif transaction_count < developing_threshold:
            return ProfileStatus.DEVELOPING
        else:
            return ProfileStatus.ESTABLISHED

    @staticmethod
    def compare_transaction(
        profile: UserBehaviourProfile,
        transaction: Any,
        current_device: Optional[Any] = None,
    ) -> BehaviourComparison:
        """
        Compare an incoming transaction against established profile baselines.
        Does NOT compute fraud scores.
        """
        amt_raw = _safe_get(transaction, "amount")
        amount = float(amt_raw) if amt_raw is not None else 0.0

        # Amount comparison
        amount_within_normal = True
        ratio = None
        if profile.average_transaction_amount and profile.average_transaction_amount > 0:
            ratio = round(amount / profile.average_transaction_amount, 2)
            if profile.normal_amount_upper_bound is not None:
                amount_within_normal = amount <= profile.normal_amount_upper_bound

        # Location comparison
        city = _safe_get(transaction, "city")
        country = _safe_get(transaction, "country")
        loc_known = True
        if (city or country) and profile.known_locations:
            loc_label = f"{city}, {country}" if country else str(city)
            loc_known = any(
                str(city).strip().lower() in k.lower()
                for k in profile.known_locations
                if city
            )

        # Device comparison
        dev_id = _safe_get(transaction, "device_id")
        dev_fp = _safe_get(current_device, "fingerprint") if current_device else None
        dev_known = True
        if profile.known_devices > 0:
            dev_known = False
            if dev_id and str(dev_id) in profile.known_device_ids:
                dev_known = True
            elif dev_fp and str(dev_fp) in profile.known_device_fingerprints:
                dev_known = True

        # Merchant comparison
        cat = _safe_get(transaction, "merchant_category")
        m_name = _safe_get(transaction, "merchant_name")
        merch_known = True
        if profile.known_categories or profile.known_merchants:
            merch_known = False
            if cat and any(str(cat).strip().lower() == k.lower() for k in profile.known_categories):
                merch_known = True
            elif m_name and any(str(m_name).strip().lower() == k.lower() for k in profile.known_merchants):
                merch_known = True

        # Time comparison
        time_normal = True
        txn_time = _parse_datetime(_safe_get(transaction, "timestamp"))
        if txn_time and profile.normal_transaction_start_hour is not None and profile.normal_transaction_end_hour is not None:
            h = txn_time.hour
            # Simple boundary check with 1 hr buffer
            start_b = max(0, profile.normal_transaction_start_hour - 1)
            end_b = min(23, profile.normal_transaction_end_hour + 1)
            time_normal = start_b <= h <= end_b

        return BehaviourComparison(
            amount_within_normal_range=amount_within_normal,
            location_is_known=loc_known,
            device_is_known=dev_known,
            merchant_is_known=merch_known,
            time_is_normal=time_normal,
            amount_vs_average_ratio=ratio,
            details={
                "profile_status": profile.profile_status.value,
                "historical_txns": profile.profile_transaction_count,
            },
        )

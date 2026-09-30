"""User Behaviour Profile Service retrieving historical activity and calculating baselines."""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.config import Settings, get_settings
from app.logging_config import logger
from app.models.user import User
from app.models.transaction import Transaction
from app.models.device import Device
from app.models.login_attempt import LoginAttempt
from app.behaviour.models import BehaviourComparison, UserBehaviourProfile
from app.behaviour.calculator import BehaviourProfileCalculator


class UserBehaviourProfileService:
    """
    Data-access and orchestration service computing behavioural profiles
    from stored historical activity.
    """

    def __init__(self, db: Session, settings: Optional[Settings] = None):
        self.db = db
        self.settings = settings or get_settings()
        self.calculator = BehaviourProfileCalculator()

    def get_user_profile(
        self,
        user_id: str,
        before_time: Optional[datetime] = None,
        exclude_transaction_id: Optional[str] = None,
    ) -> Optional[UserBehaviourProfile]:
        """
        Build behavioural profile for a user using historical data up to `before_time`.
        Excludes `exclude_transaction_id` so the current transaction does not distort its own baseline.
        Returns None if user does not exist.
        """
        user = self.db.get(User, user_id)
        if not user:
            logger.warning(f"Cannot generate behaviour profile: user '{user_id}' not found")
            return None

        ref_time = before_time or datetime.now(timezone.utc)
        lookback_days = int(self.settings.BEHAVIOUR_PROFILE_DAYS)
        window_start = ref_time - timedelta(days=lookback_days)

        logger.debug(
            f"Computing behaviour profile for user={user_id} over past {lookback_days} days "
            f"(window: {window_start} to {ref_time})"
        )

        # 1. Fetch historical transactions within window
        txn_stmt = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.timestamp >= window_start,
                Transaction.timestamp <= ref_time,
            )
        )
        if exclude_transaction_id:
            txn_stmt = txn_stmt.where(Transaction.id != exclude_transaction_id)
        txn_stmt = txn_stmt.order_by(Transaction.timestamp.desc())
        historical_txns: List[Transaction] = list(self.db.scalars(txn_stmt).all())

        # 2. Fetch known devices
        dev_stmt = select(Device).where(Device.user_id == user_id).order_by(Device.last_seen_at.desc())
        known_devices: List[Device] = list(self.db.scalars(dev_stmt).all())

        # 3. Fetch login attempts within window
        login_stmt = (
            select(LoginAttempt)
            .where(
                LoginAttempt.user_id == user_id,
                LoginAttempt.timestamp >= window_start,
                LoginAttempt.timestamp <= ref_time,
            )
            .order_by(LoginAttempt.timestamp.desc())
        )
        login_attempts: List[LoginAttempt] = list(self.db.scalars(login_stmt).all())

        # 4. Extract data lists for calculator
        amounts = [float(t.amount) for t in historical_txns if t.amount is not None]
        timestamps = [t.timestamp for t in historical_txns if t.timestamp is not None]

        # 5. Compute metrics
        mult = float(self.settings.PROFILE_AMOUNT_RANGE_MULTIPLIER)
        avg_amt, min_amt, max_amt, lower_amt, upper_amt, amt_range = (
            self.calculator.calculate_amount_metrics(amounts, multiplier=mult)
        )

        avg_daily_txns, active_days, total_txns = self.calculator.calculate_frequency_metrics(
            timestamps, period_days=lookback_days
        )

        start_h, end_h, time_window = self.calculator.calculate_hours_metrics(timestamps)

        min_loc_count = int(self.settings.PROFILE_LOCATION_MIN_COUNT)
        known_locations, detailed_locs = self.calculator.calculate_location_metrics(
            historical_txns, min_count=min_loc_count
        )

        known_merchants, known_categories, detailed_merchants = (
            self.calculator.calculate_merchant_metrics(historical_txns)
        )

        device_count, device_ids, device_fps, detailed_devices = (
            self.calculator.calculate_device_metrics(known_devices, historical_txns)
        )

        failed_logins, recent_failed, latest_failed = self.calculator.calculate_login_metrics(
            login_attempts,
            period_start=window_start,
            recent_window_minutes=15,
            now=ref_time,
        )

        status = self.calculator.determine_profile_status(
            total_txns,
            insufficient_threshold=int(self.settings.PROFILE_INSUFFICIENT_THRESHOLD),
            developing_threshold=int(self.settings.PROFILE_DEVELOPING_THRESHOLD),
        )

        profile = UserBehaviourProfile(
            user_id=user_id,
            profile_status=status,
            average_transaction_amount=avg_amt,
            minimum_transaction_amount=min_amt,
            maximum_transaction_amount=max_amt,
            normal_amount_lower_bound=lower_amt,
            normal_amount_upper_bound=upper_amt,
            normal_amount_range=amt_range,
            average_transactions_per_day=avg_daily_txns,
            total_active_days=active_days,
            profile_transaction_count=total_txns,
            normal_transaction_start_hour=start_h,
            normal_transaction_end_hour=end_h,
            normal_transaction_hours=time_window,
            known_locations=known_locations,
            detailed_locations=detailed_locs,
            known_merchants=known_merchants,
            known_categories=known_categories,
            detailed_merchants=detailed_merchants,
            known_devices=device_count,
            known_device_ids=device_ids,
            known_device_fingerprints=device_fps,
            detailed_devices=detailed_devices,
            failed_login_count=failed_logins,
            recent_failed_login_count=recent_failed,
            latest_failed_login_at=latest_failed,
            profile_period_days=lookback_days,
            profile_period_start=window_start,
            profile_period_end=ref_time,
        )

        logger.info(
            f"User '{user_id}' behaviour profile: status={status.value}, "
            f"txns={total_txns}, avg_amount={avg_amt}, active_days={active_days}"
        )
        return profile

    def compare_transaction(
        self,
        user_id: str,
        transaction: Any,
        current_device: Optional[Any] = None,
        profile: Optional[UserBehaviourProfile] = None,
    ) -> Optional[BehaviourComparison]:
        """Compare a transaction against user's profile, generating comparison flags."""
        prof = profile or self.get_user_profile(user_id)
        if not prof:
            return None
        return self.calculator.compare_transaction(prof, transaction, current_device)

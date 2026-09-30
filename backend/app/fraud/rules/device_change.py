"""Device Change Fraud Rule."""

from typing import Set
from app.fraud.base import FraudRule
from app.fraud.context import RuleContext, _safe_get
from app.fraud.result import RuleResult


class DeviceChangeRule(FraudRule):
    """
    Detects transactions originating from an unfamiliar or previously unseen client device.
    Uses software-based hardware/browser cryptographic fingerprints and device IDs.
    """

    @property
    def rule_id(self) -> str:
        return "device_change"

    @property
    def name(self) -> str:
        return "Device Change"

    @property
    def description(self) -> str:
        return "Flags transactions originating from an unfamiliar or unrecognized device."

    @property
    def default_score_contribution(self) -> float:
        return 15.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        # Determine current device details
        current_dev = context.current_device
        curr_device_id = context.get_transaction_field("device_id")
        curr_fingerprint = None

        if current_dev:
            curr_device_id = (
                curr_device_id
                or _safe_get(current_dev, "device_id")
                or _safe_get(current_dev, "id")
            )
            curr_fingerprint = _safe_get(current_dev, "fingerprint")

        # Collect known device identifiers
        known_device_ids: Set[str] = set()
        known_fingerprints: Set[str] = set()

        for dev in context.known_devices:
            dev_id = _safe_get(dev, "device_id") or _safe_get(dev, "id")
            dev_fp = _safe_get(dev, "fingerprint")
            if dev_id:
                known_device_ids.add(str(dev_id))
            if dev_fp:
                known_fingerprints.add(str(dev_fp))

        # Check if pre-computed UserBehaviourProfile is present in context
        prof = getattr(context, "user_profile", None)
        if prof and hasattr(prof, "known_device_ids"):
            known_device_ids.update(prof.known_device_ids)
            known_fingerprints.update(prof.known_device_fingerprints)

        # Check for missing telemetry
        if not curr_device_id and not curr_fingerprint:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="No device identifier or fingerprint provided for the current transaction.",
                evidence={"status": "missing_device_telemetry"},
                score_contribution=0.0,
            )

        # Baseline: If user has no prior recorded devices, don't flag as anomaly
        if not known_device_ids and not known_fingerprints:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                reason="Initial transaction for user; no prior baseline devices on record.",
                evidence={
                    "known_devices_count": 0,
                    "is_new_device": True,
                    "current_device_id": curr_device_id,
                },
                score_contribution=0.0,
            )

        # Check if matched against known devices
        matched = False
        if curr_fingerprint and curr_fingerprint in known_fingerprints:
            matched = True
        elif curr_device_id and curr_device_id in known_device_ids:
            matched = True

        is_new_device = not matched
        triggered = is_new_device

        # Check for compound threat signal: New Device + New Location
        curr_city = context.get_transaction_field("city") or context.get_transaction_field("location_city")
        curr_country = context.get_transaction_field("country") or context.get_transaction_field("location_country")
        is_new_location = False

        if is_new_device and (curr_city or curr_country):
            known_locations: Set[str] = set()
            if prof and hasattr(prof, "known_locations"):
                for loc in prof.known_locations:
                    known_locations.add(str(loc).lower())
            for h_tx in context.historical_transactions:
                hc = _safe_get(h_tx, "city") or _safe_get(h_tx, "location_city")
                hco = _safe_get(h_tx, "country") or _safe_get(h_tx, "location_country")
                if hc:
                    known_locations.add(str(hc).lower())
                if hco:
                    known_locations.add(str(hco).lower())

            if known_locations:
                city_matched = curr_city and any(str(curr_city).lower() in k for k in known_locations)
                country_matched = curr_country and any(str(curr_country).lower() in k for k in known_locations)
                if not city_matched and not country_matched:
                    is_new_location = True

        if triggered:
            if is_new_location:
                loc_desc = f"{curr_city}, {curr_country}" if curr_country else str(curr_city)
                reason = (
                    f"Transaction originated from an unfamiliar device "
                    f"(device_id={curr_device_id or 'unknown'}, fingerprint={curr_fingerprint or 'none'}) "
                    f"combined with an unrecognized location ({loc_desc})."
                )
            else:
                reason = (
                    f"Transaction originated from an unfamiliar device "
                    f"(device_id={curr_device_id or 'unknown'}, fingerprint={curr_fingerprint or 'none'})."
                )
            score = self.default_score_contribution
        else:
            reason = "Transaction device is recognized and verified in user profile history."
            score = 0.0

        evidence = {
            "current_device_id": curr_device_id,
            "current_fingerprint": curr_fingerprint,
            "known_devices_count": len(known_device_ids) or len(context.known_devices),
            "is_new_device": is_new_device,
            "is_new_location": is_new_location,
            "new_device_new_location": is_new_device and is_new_location,
        }

        if current_dev:
            evidence["is_vpn"] = bool(_safe_get(current_dev, "is_vpn", False))
            evidence["is_tor"] = bool(_safe_get(current_dev, "is_tor", False))
            evidence["is_emulator"] = bool(_safe_get(current_dev, "is_emulator", False))

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason=reason,
            evidence=evidence,
            score_contribution=score,
        )

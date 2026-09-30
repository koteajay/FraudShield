# FraudShield — Explainable Fraud Detection & Reviewer Platform

FraudShield is an explainable fraud detection and investigation platform designed to assess transaction risk, highlight fraudulent patterns with transparent explanations, and provide reviewer workflows.

> **Status: Phase 11 — "Why Flagged?" Investigation UI Complete**  
> This repository contains the complete persistence layer (Phase 2), modular fraud rule engine (Phase 3), explainable risk scoring service (Phase 4), user behaviour profiling (Phase 5), software-based device tracking (Phase 6), account takeover correlation detection (Phase 7), chronological transaction journey timelines (Phase 8), full REST API layer (Phase 9), complete React Reviewer Console (Phase 10), and deep explainable transaction investigation screen (Phase 11).

---

## 🧠 Phase 3 — Fraud Rule Engine Architecture

FraudShield implements a modular, extensible fraud rule evaluation engine where rules operate independently on domain data. The core engine contains **zero rule-specific business logic** and evaluates any rule implementing the `FraudRule` contract.

```
                    ┌─────────────────────────┐
                    │       RuleContext       │
                    │ (Txn, User, History,    │
                    │  Devices, Logins, Cfg)  │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FraudRuleEngine     │
                    └────────────┬────────────┘
                                 │ pulls rules
                                 ▼
                    ┌─────────────────────────┐
                    │      RuleRegistry       │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  VelocityRule    │    │AmountSpikeRule   │    │ ImpossibleGeoRule│ ... (8 rules)
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │    List[RuleResult]     │
                    │ (Standardized outputs)  │
                    └─────────────────────────┘
```

### 1. Base Components

- **`FraudRule` ([app/fraud/base.py](backend/app/fraud/base.py))**: Abstract base class defining `rule_id`, `name`, `description`, `default_score_contribution`, and `evaluate(context: RuleContext) -> RuleResult`.
- **`RuleContext` ([app/fraud/context.py](backend/app/fraud/context.py))**: Decoupled domain context containing the current transaction, user profile, recent transactions, historical transactions, known devices, login attempts, and configurable thresholds.
- **`RuleResult` ([app/fraud/result.py](backend/app/fraud/result.py))**: Standardized output structure returned by every rule.
- **`RuleRegistry` ([app/fraud/registry.py](backend/app/fraud/registry.py))**: Thread-safe registry for registering, unregistering, and retrieving active rules.
- **`FraudRuleEngine` ([app/fraud/engine.py](backend/app/fraud/engine.py))**: Executes all registered rules against a given `RuleContext`. It safely catches and isolates exceptions per rule, never crashing the engine, and does **not** calculate final aggregate risk scores (Phase 4).

### 2. Standardized Rule Result Format

Every rule returns the exact same structure:
```json
{
  "rule_id": "transaction_velocity",
  "rule_name": "Transaction Velocity",
  "triggered": true,
  "reason": "More than 5 transactions occurred within 5 minutes (7 detected).",
  "evidence": {
    "transaction_count": 7,
    "window_minutes": 5,
    "threshold": 5
  },
  "score_contribution": 25.0
}
```

### 3. All 8 Implemented Fraud Rules

1. **Transaction Velocity Rule** (`transaction_velocity`): Detects burst transaction volume within sliding time windows (default: >5 txns in 5 mins).
2. **Unusual Transaction Amount Rule** (`unusual_transaction_amount`): Detects transactions significantly larger than historical average spend (default: >3.0x average).
3. **Impossible Geographical Location Rule** (`impossible_geographical_location`): Calculates great-circle Haversine distance and elapsed time between consecutive transactions; flags speeds exceeding realistic thresholds (default: >900 km/h).
4. **Device Change Rule** (`device_change`): Detects transactions originating from unrecognized hardware/browser cryptographic fingerprints.
5. **Unusual Time Rule** (`unusual_transaction_time`): Flags transactions occurring outside established historical user active hours.
6. **Multiple Failed Login Rule** (`multiple_failed_logins`): Detects credential stuffing or brute force attempts preceding a transaction (default: ≥3 failed logins in 10 mins).
7. **Unusual Merchant Rule** (`unusual_merchant`): Detects transactions in merchant categories completely unseen in user history.
8. **Blacklisted Country Rule** (`blacklisted_country`): Detects transactions involving configured restricted demo jurisdictions (default: `["PRK", "IRN", "SYR", "CUB", "RUS"]`).

---

## 🔌 How to Add a New Rule (Extensibility)

New rules can be implemented and registered **without modifying a single line of the core engine**:

```python
from app.fraud import FraudRule, RuleContext, RuleResult, create_default_engine

# 1. Define custom rule implementing FraudRule
class NewDeviceLocationRule(FraudRule):
    @property
    def rule_id(self) -> str:
        return "new_device_location"

    @property
    def name(self) -> str:
        return "New Device Location Discrepancy"

    @property
    def default_score_contribution(self) -> float:
        return 20.0

    def evaluate(self, context: RuleContext) -> RuleResult:
        curr_device = context.current_device
        country = context.get_transaction_field("country")
        
        # Safe evaluation logic on domain context
        triggered = curr_device is not None and country == "UNKNOWN"
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=triggered,
            reason="Unrecognized device in unknown location" if triggered else "Location verified",
            evidence={"country": country},
            score_contribution=self.default_score_contribution if triggered else 0.0,
        )

# 2. Register with engine
engine = create_default_engine()
engine.registry.register(NewDeviceLocationRule())

# 3. Evaluate context — engine automatically executes the new rule!
results = engine.evaluate(context)
```

---

## ⚙️ Configuration Variables

Thresholds are centrally configurable in `.env` and `app/config.py`:

```bash
# Velocity Rule
VELOCITY_THRESHOLD_COUNT=5
VELOCITY_WINDOW_MINUTES=5

# Amount Rule
UNUSUAL_AMOUNT_MULTIPLIER=3.0
UNUSUAL_AMOUNT_MIN_HISTORY=3
UNUSUAL_AMOUNT_MIN_THRESHOLD=100.0

# Impossible Travel Rule
IMPOSSIBLE_TRAVEL_MAX_SPEED_KMH=900.0

# Time & Login Rules
UNUSUAL_TIME_MIN_HISTORY=5
UNUSUAL_TIME_BUFFER_HOURS=1
FAILED_LOGIN_THRESHOLD=3
FAILED_LOGIN_WINDOW_MINUTES=10

# Merchant & Country Rules
UNUSUAL_MERCHANT_MIN_HISTORY=3
BLACKLISTED_COUNTRIES=["PRK","IRN","SYR","CUB","RUS"]
```

---

## 🧪 Running Rule Tests

Run the full test suite (50 tests covering Phase 1, Phase 2 models & repositories, and Phase 3 rules & engine):

```bash
cd backend
pytest -v
```

To run only Phase 3 rule and engine tests:
```bash
pytest backend/tests/test_fraud_rules.py backend/tests/test_fraud_engine.py -v
```

---

## ⚖️ Phase 4 — Risk Scoring & Explainability Architecture

The Phase 4 Risk Scoring layer aggregates the standardized outputs of the Phase 3 rule engine into an explainable, bounded final score without modifying or re-evaluating the underlying fraud detection rules.

```
Transaction ──► RuleContext ──► FraudRuleEngine ──► RuleResult[] ──► RiskScorer ──► RiskAssessment
                                                                                       ├── Final Score (0–100)
                                                                                       ├── Risk Level
                                                                                       ├── Triggered Rules
                                                                                       ├── Rule Contributions
                                                                                       ├── Preserved Evidence
                                                                                       └── Human Explanation
```

### 1. Default Score Contributions (Configurable)

| Fraud Rule | ID | Default Points | Config Variable |
| :--- | :--- | :---: | :--- |
| Impossible Location | `impossible_geographical_location` | **+35** | `SCORE_IMPOSSIBLE_GEOGRAPHICAL_LOCATION` |
| Unusual Amount | `unusual_transaction_amount` | **+30** | `SCORE_UNUSUAL_TRANSACTION_AMOUNT` |
| Blacklisted Country | `blacklisted_country` | **+30** | `SCORE_BLACKLISTED_COUNTRY` |
| Transaction Velocity | `transaction_velocity` | **+25** | `SCORE_TRANSACTION_VELOCITY` |
| Multiple Failed Login | `multiple_failed_login` | **+20** | `SCORE_MULTIPLE_FAILED_LOGIN` |
| Device Change | `device_change` | **+15** | `SCORE_DEVICE_CHANGE` |
| Unusual Merchant | `unusual_merchant` | **+15** | `SCORE_UNUSUAL_MERCHANT` |
| Unusual Time | `unusual_time` | **+10** | `SCORE_UNUSUAL_TIME` |

### 2. Risk Level Thresholds

Categorical risk classification is centrally mapped and strictly validated (`0 <= LOW < MEDIUM < HIGH <= 100`):

| Risk Level | Score Range | Review Disposition Recommendation |
| :---: | :---: | :--- |
| **LOW** | `0 – 29` | Automated approval, minimal friction |
| **MEDIUM** | `30 – 59` | Step-up verification or elevated monitoring |
| **HIGH** | `60 – 79` | Manual investigation queue |
| **CRITICAL** | `80 – 100` | Immediate transaction block or freeze |

### 3. Bounded Calculation & Deduplication Guarantees

- **Bounding**: Final score is clamped safely within `[0.0, 100.0]`. If cumulative points exceed 100 (e.g. 35 + 30 + 25 + 20 = 110), the final score is capped at `100.0`.
- **Triggered-Only Contributions**: Only rules with `triggered == True` add to the score. Non-triggered rules contribute exactly `0.0`.
- **Deduplication**: If an upstream bug delivers multiple results for the same `rule_id`, each rule contributes at most once.
- **Evidence Preservation**: Forensic parameters (metrics, thresholds, speed, lat/lon, attempt counts) from Phase 3 rules are passed forward untouched in the `evidence` payload.

### 4. Standardized `RiskAssessment` Output

```json
{
  "final_score": 90.0,
  "risk_level": "CRITICAL",
  "triggered_rules": [
    "transaction_velocity",
    "unusual_transaction_amount",
    "impossible_geographical_location"
  ],
  "rule_contributions": [
    {
      "rule_id": "transaction_velocity",
      "rule_name": "Transaction Velocity",
      "score": 25.0,
      "reason": "More than 5 transactions occurred within 5 minutes (7 detected).",
      "evidence": { "transaction_count": 7, "window_minutes": 5, "threshold": 5 }
    },
    {
      "rule_id": "unusual_transaction_amount",
      "rule_name": "Unusual Transaction Amount",
      "score": 30.0,
      "reason": "Transaction amount ($1500.00) exceeds 3.0x the historical average.",
      "evidence": { "current_amount": 1500.0, "historical_average": 50.0, "comparison_ratio": 30.0 }
    },
    {
      "rule_id": "impossible_geographical_location",
      "rule_name": "Impossible Geographical Location",
      "score": 35.0,
      "reason": "Required travel speed of 3750.0 km/h between locations exceeds maximum realistic threshold.",
      "evidence": { "distance_km": 1250.0, "elapsed_minutes": 20.0, "required_speed_kmh": 3750.0 }
    }
  ],
  "evidence": {
    "transaction_velocity": { "transaction_count": 7, "window_minutes": 5, "threshold": 5 },
    "unusual_transaction_amount": { "current_amount": 1500.0, "historical_average": 50.0 },
    "impossible_geographical_location": { "distance_km": 1250.0, "required_speed_kmh": 3750.0 }
  },
  "explanation": "Transaction classified as CRITICAL risk with a score of 90. The following 3 suspicious patterns were detected: Transaction Velocity (+25), Unusual Transaction Amount (+30), and Impossible Geographical Location (+35)."
}
```

### 5. Deterministic Human-Readable Explanations

The explanation engine (`app/fraud/scoring/explanations.py`) runs **completely locally without AI/LLM dependencies**:
- **Zero Triggers**: `"No suspicious rule conditions were triggered for this transaction. The transaction currently has a low risk score of 0."`
- **Single Trigger**: `"Transaction classified as MEDIUM risk with a score of 30. The Unusual Transaction Amount rule was triggered: Transaction amount ($1500.00) exceeds 3.0x the historical average."`
- **Multiple Triggers**: Synthesizes rule titles and itemized point additions into reviewer-friendly summaries without claiming absolute certainty of fraud.

---

## 👤 Phase 5 — User Behaviour Profile

> **Important**: The behaviour profile describes historical patterns. It does not independently determine fraud.

The User Behaviour Profile system constructs a deterministic, explainable behavioural baseline for each user by analyzing historical transactions, device access telemetry, locations, and authentication attempts.

### 1. Conceptual Architecture

```text
Historical Transactions / Logins / Devices
                 ↓
    UserBehaviourProfileService
                 ↓
       UserBehaviourProfile
                 ↓
            RuleContext
                 ↓
      FraudRuleEngine (Rules consume profile metrics)
                 ↓
          RiskAssessment
```

### 2. Metrics Tracked

| Metric Category | Metrics Computed | Details |
| :--- | :--- | :--- |
| **Transaction Amount** | `average_transaction_amount`, `minimum_transaction_amount`, `maximum_transaction_amount`, `normal_amount_lower_bound`, `normal_amount_upper_bound` | Deterministic bounds calculated using configurable multiplier around average (default `1.5x`). |
| **Frequency** | `average_transactions_per_day`, `total_active_days`, `profile_transaction_count` | Activity density over the historical window. |
| **Active Hours** | `normal_transaction_start_hour`, `normal_transaction_end_hour`, `normal_transaction_hours` | Earliest and latest hours of historical activity, accounting for midnight boundary wrapping. |
| **Locations** | `known_locations`, `detailed_locations` | Cities and countries with observation frequency counts (configurable min occurrences). |
| **Merchants** | `known_merchants`, `known_categories`, `detailed_merchants` | Frequented merchant entities and business categories. |
| **Devices** | `known_devices`, `known_device_ids`, `known_device_fingerprints`, `detailed_devices` | Count and cryptographic fingerprints of enrolled and observed devices. |
| **Authentication Telemetry** | `failed_login_count`, `recent_failed_login_count`, `latest_failed_login_at` | Failed logins over the 30-day window and recent 15-minute sliding window. |

### 3. Historical Window & Current Transaction Isolation

- **Configurable Window**: Default lookback of 30 days (`BEHAVIOUR_PROFILE_DAYS=30`).
- **Baseline Isolation**: The current transaction being evaluated is **explicitly excluded** via `exclude_transaction_id` and `before_time` so a suspicious transaction cannot distort the baseline used to evaluate itself.

### 4. Data Sufficiency & Profile Confidence Tiers

Profiles are tagged with deterministic confidence statuses based on transaction sample size:
- `INSUFFICIENT_DATA`: 0–4 transactions (rules fall back safely or abstain from false alarms).
- `DEVELOPING`: 5–19 transactions (baseline is emerging).
- `ESTABLISHED`: 20+ transactions (robust behavioral baseline).

### 5. Current Transaction Comparison

`UserBehaviourProfile.compare_transaction(transaction)` generates a `BehaviourComparison` struct:
- `amount_within_normal_range`: boolean
- `location_is_known`: boolean
- `device_is_known`: boolean
- `merchant_is_known`: boolean
- `time_is_normal`: boolean
- `amount_vs_average_ratio`: float (e.g. 16.67x)

### 6. API Endpoint

```http
GET /api/users/{user_id}/behaviour-profile
```

**Example Response**:
```json
{
  "user_id": "user_1024",
  "profile_status": "ESTABLISHED",
  "average_transaction_amount": 3200.0,
  "minimum_transaction_amount": 1000.0,
  "maximum_transaction_amount": 5500.0,
  "normal_amount_range": {
    "min": 1600.0,
    "max": 5500.0
  },
  "average_transactions_per_day": 4.0,
  "normal_transaction_hours": {
    "start": "08:00",
    "end": "22:00",
    "start_hour": 8,
    "end_hour": 22
  },
  "known_locations": [
    "Hyderabad, IN",
    "Bengaluru, IN"
  ],
  "known_merchants": [
    "Amazon",
    "Swiggy",
    "Uber"
  ],
  "known_categories": [
    "Shopping",
    "Food",
    "Transportation"
  ],
  "known_devices": 2,
  "failed_login_count": 2,
  "recent_failed_login_count": 0,
  "profile_transaction_count": 28,
  "profile_period_days": 30,
  "profile_period_start": "2026-08-31T14:00:00Z",
  "profile_period_end": "2026-09-30T14:00:00Z"
}
```

---

## 📱 Phase 6 — Device Fingerprinting & Device Change Detection

FraudShield incorporates a **100% software-based device tracking and identification system**.

> **Important**: This architecture requires **NO IoT hardware, NO sensors, NO external paid APIs, and NO third-party fingerprinting services**. It relies entirely on client-presented persistent application device IDs and lightweight HTTP header telemetry parsing.

### 1. Tracked Device Telemetry

| Field | Source / Strategy | Description |
| :--- | :--- | :--- |
| `device_id` | Application-level persistent ID (e.g. browser `localStorage` UUID) | Consistent identifier presented by the client application. |
| `browser` | Lightweight User-Agent parser | Extracts Chrome, Firefox, Safari, Edge, Opera, or "Unknown". |
| `operating_system` | Lightweight User-Agent parser | Extracts Windows, macOS, Linux, Android, iOS, or "Unknown". |
| `ip_address` | Request client socket or trusted proxy header | Client IP address recorded during interactions. |
| `user_agent` | Raw `User-Agent` HTTP header | Full client telemetry string. |
| `first_seen_at` | Initial registration timestamp | Set when device is first encountered; **never overwritten**. |
| `last_seen_at` | Subsequent activity timestamp | Updated on every transaction or interaction from this device. |
| `is_known` / `is_new_device` | DeviceService detection | Deterministic boolean flag signaling recognized vs unfamiliar client. |

### 2. Conceptual Architecture

```text
Incoming Request Telemetry (User-Agent, IP, Device ID)
                       ↓
               DeviceService
                       ↓
         Find (user_id + device_id)
                       ↓
         Existing?
        ┌───────────────┐
        │ YES           │ NO
        ↓               ↓
   Known Device     New Device
   Update last_seen Register Device
        ↓               ↓
   Normal Signal   Risk Signal (+15)
                        ↓
                 New Location?
                 ┌───────────────┐
                 │ YES           │ NO
                 ↓               ↓
         Compound Threat     Standard New Device
         ("New Device +      (+15 pts)
          New Location")
```

### 3. Integration with Fraud Engine (`DeviceChangeRule`)

- **Known Device**: Recognized in user's device history; returns `triggered = False` with `score_contribution = 0.0`.
- **New Device**: Unseen for this user; returns `triggered = True` with `score_contribution = 15.0`.
- **New Device + New Location**: Compound threat signal when an unrecognized device executes a transaction in an unfamiliar city/country. Adds `"new_device_new_location": True` to evidence with explicit explanatory attribution.
- **Initial Baseline**: Users with zero historical devices do not trigger false-positive anomalies on their initial transaction.

### 4. API Endpoints

- `GET /api/users/{user_id}/devices`: Retrieve all enrolled/observed devices for a user.
- `POST /api/users/{user_id}/devices`: Register a new device or refresh `last_seen_at` for an existing device.
- `GET /api/users/{user_id}/devices/{device_id}`: Fetch detailed device telemetry for a specific device.

---

## 🕵️ Phase 7 — Unusual Time & Account Takeover (ATO) Detection

Phase 7 introduces specialized time-pattern anomaly detection and a dedicated **Account Takeover (ATO) Correlation Layer**. ATO detection correlates multiple suspicious signals across independent fraud detection dimensions to evaluate compound takeover risk without altering individual rule evaluations or overriding the Phase 4 overall transaction risk score.

```
Historical User Data ──► User Behaviour Profile ──► Device Information
                                                            │
                                                            ▼
                                                    Current Transaction
                                                            │
                                                            ▼
                                                    Fraud Rule Engine
                                                            │
                                                            ▼
                                                 Individual Rule Results
                                                            │
                                                            ▼
                                                Account Takeover Detector
                                                            │
                                                            ▼
                                                      ATO Assessment
                                                            │
                                                            ▼
                                                   Phase 4 Risk Scoring
```

### 1. Unusual Time Detection (`UnusualTimeRule`)

- **Profile Consumption**: Compares transaction execution time against the user's established historical activity window (`normal_transaction_start_hour` and `normal_transaction_end_hour`) calculated in `UserBehaviourProfile`.
- **Overnight Window Support**: Correctly evaluates windows that cross midnight (e.g. `22:00` to `04:00`). Using modulo-24 cyclic hour sets ensures `23:30` and `02:00` are recognized as normal while `12:00` triggers an anomaly.
- **Timezone Awareness**: Converts transaction timestamps using explicitly provided transaction timezones or user profile timezones before comparison. Fallbacks seamlessly to UTC when timezones are omitted.
- **Insufficient History Safety**: If fewer than `UNUSUAL_TIME_MIN_HISTORY` (default 5) transactions exist, or the profile status is `INSUFFICIENT_DATA`, the rule returns `triggered = False` with a clear explanation without fabricating a baseline.
- **Evidence Preservation**: Adheres strictly to the standard Phase 3 `RuleResult` format:
  ```json
  {
    "rule_id": "unusual_time",
    "rule_name": "Unusual Transaction Time",
    "triggered": true,
    "reason": "Transaction initiated at 03:15 is outside the user's regular activity hours (08:00–22:00).",
    "evidence": {
      "transaction_time": "03:15",
      "normal_start": "08:00",
      "normal_end": "22:00",
      "outside_normal_hours": true,
      "current_hour": 3,
      "buffer_hours": 1
    },
    "score_contribution": 10.0
  }
  ```

---

### 2. Account Takeover Detection (`AccountTakeoverDetector`)

The `AccountTakeoverDetector` consumes existing rule results, profile data, and device information to correlate **5 suspicious signals**:

| # | ATO Signal Indicator | Detection Logic & Source |
| :-: | :--- | :--- |
| **1** | `new_device` | Triggered when `DeviceChangeRule` detects an unfamiliar device ID. |
| **2** | `new_location` | Triggered when current transaction city/country does not match `UserBehaviourProfile.known_locations`, or when `ImpossibleLocationRule` triggers. |
| **3** | `unusual_time` | Triggered when `UnusualTimeRule` detects transaction outside established active hours. |
| **4** | `failed_login` | Triggered when `MultipleFailedLoginRule` triggers, or recent failed logins within `ATO_FAILED_LOGIN_WINDOW_MINUTES` meet `ATO_FAILED_LOGIN_THRESHOLD`. |
| **5** | `unusual_transaction` | Triggered when `UnusualAmountRule` detects an abnormal spike above user spending patterns. |

#### Tri-State Evaluation (`TRUE`, `FALSE`, `UNKNOWN`)
To prevent false-positive inflation on new accounts or telemetry-sparse requests, missing data (e.g. absent device headers or unestablished location profiles) is classified as `SignalStatus.UNKNOWN` rather than `FALSE`. **Only definitive `TRUE` signals increment the ATO `signal_count`.**

#### Deterministic ATO Severity Thresholds
ATO risk levels are evaluated independently of transaction scores via configurable thresholds:
- **0–1 signals**: `LOW` (`is_at_risk = False`)
- **2 signals**: `MEDIUM` (`is_at_risk = True`)
- **3 signals**: `HIGH` (`is_at_risk = True`)
- **4–5 signals**: `CRITICAL` (`is_at_risk = True`)

> **False-Positive Safety Disclaimer**: ATO risk is a suspicious-pattern indicator designed to prioritize security investigations. It reports *"Potential account takeover risk detected"* and **never** makes definitive claims of account compromise.

#### Structured ATO Assessment Model (`AccountTakeoverAssessment`)
```json
{
  "user_id": "U1024",
  "transaction_id": "TX-1001",
  "is_at_risk": true,
  "risk_level": "CRITICAL",
  "signal_count": 5,
  "signals": {
    "new_device": true,
    "new_location": true,
    "unusual_time": true,
    "failed_login": true,
    "unusual_transaction": true
  },
  "signal_statuses": {
    "new_device": "true",
    "new_location": "true",
    "unusual_time": "true",
    "failed_login": "true",
    "unusual_transaction": "true"
  },
  "triggered_rules": [
    "device_change",
    "unusual_time",
    "multiple_failed_login",
    "unusual_transaction_amount"
  ],
  "evidence": {
    "new_device": { "device_id": "DEV-NEW", "is_known": false },
    "new_location": { "current_location": "Moscow, RU", "known_locations": ["Hyderabad, IN"] },
    "unusual_time": { "transaction_time": "03:15", "normal_start": "08:00", "normal_end": "22:00" },
    "failed_login": { "failed_attempts": 4, "window_minutes": 30 },
    "unusual_transaction": { "amount": 95000.0, "normal_range": "2000–8000" }
  },
  "explanation": "Potential account takeover risk is CRITICAL because 5 suspicious signals were detected: new device, unfamiliar location, unusual transaction time, recent failed login activity, and unusual transaction amount."
}
```

### 3. API Endpoints

---

## 🧭 Phase 8 — Chronological Transaction Journey

Phase 8 introduces the **Transaction Journey**, an aggregation and chronological storytelling layer that allows fraud reviewers to inspect the complete context surrounding any transaction.

```
       Surrounding User Activity Window (e.g. ±30 minutes)
   ┌────────────────────────────────────────────────────────┐
   │ 10:02 → Hyderabad → ₹2,000  → Device A (Normal)        │
   │ 10:15 → Hyderabad → ₹3,500  → Device A (Normal)        │
   │ 10:20 → New Device Encountered: Device X               │
   │ 10:21 → Delhi     → ₹75,000 → Device X ⚠️ (CRITICAL)   │
   │         ├── Unusual Amount                             │
   │         ├── Device Change                              │
   │         └── Unusual Time                               │
   │ 10:23 → Delhi     → Failed Login → Device X ⚠️         │
   └────────────────────────────────────────────────────────┘
```

> **Design Principle**: The Transaction Journey is strictly an **aggregation and read feature**. It reuses persisted data models (`Transaction`, `LoginAttempt`, `Device`, `FraudRuleResult`, `FraudFlag`) without re-running fraud rules or recalculating risk scores.

### 1. Supported Event Types

| Event Type | Source Model | Trigger Condition & Content |
| :--- | :--- | :--- |
| `TRANSACTION` | `Transaction` | Exactly **one** event per transaction within window; captures amount, currency, location, device ID, risk score, and risk level. |
| `LOGIN_ATTEMPT` | `LoginAttempt` | Authentication attempts within window; captures success/failure, failure reason, device, IP/location, and suspicion flag. |
| `DEVICE_EVENT` | `Device` | Device lifecycle markers; emitted when an unrecognized device is first encountered (`first_seen_at`) within the window. |
| `RULE_TRIGGER` | `FraudRuleResult` | Individual triggered fraud rules (`is_triggered = True`) preserving rule name, reason, score contribution, and evidence. |
| `RISK_EVENT` | `FraudFlag` / `Transaction` | Raised fraud flags, elevated risk classifications (High/Critical), or Account Takeover risk detections. |

### 2. Event Ordering & Deterministic Secondary Tie-Breaker

All events are strictly ordered:
1. Primary sort: `timestamp ASC`
2. Secondary deterministic tie-breaker for identical timestamps:
   - `LOGIN_ATTEMPT` (Priority 1)
   - `DEVICE_EVENT` (Priority 2)
   - `TRANSACTION` (Priority 3)
   - `RULE_TRIGGER` (Priority 4)
   - `RISK_EVENT` (Priority 5)

### 3. Duplicate Protection

Database joins never multiply transaction events. A transaction with 3 triggered rules produces:
- Exactly **1** `TRANSACTION` event
- Exactly **3** distinct `RULE_TRIGGER` events attached to that transaction reference

### 4. API Endpoints

- `GET /api/transactions/{transaction_id}/journey`
  - Query parameters:
    - `before_minutes` (default `30`, min `0`)
    - `after_minutes` (default `30`, min `0`)
  - Validations:
    - `400 Bad Request` if `before_minutes < 0` or `after_minutes < 0`
    - `404 Not Found` if transaction does not exist
    - `200 OK` with normalized `TransactionJourneyResponse`

### 5. Frontend Vertical Timeline Component

Implemented in `frontend/src/components/transaction-journey/`:
- **`TransactionJourney.tsx`**: Interactive investigation interface with transaction lookup, configurable time window inputs, high-level summary cards, and new-device alert banners.
- **`JourneyEventItem.tsx`**: Rich vertical timeline node rendering time badges, severity colors, location/device tags, and expandable reviewer telemetry drawers.
- **`journeyService.ts`**: TypeScript client service for fetching journey timelines.

---

## 🧪 Phase Acceptance Checklist

- [x] **Phase 1**: FastAPI foundation, SQLite DB connection, health verification, CORS, error handling
- [x] **Phase 2**: 8 core persistence models (`User`, `Device`, `Transaction`, `FraudFlag`, `FraudRuleResult`, `Review`, `Notification`, `LoginAttempt`), repositories, and Alembic migrations
- [x] **Phase 3**: Extensible Fraud Rule Engine, `RuleContext`, `RuleResult`, `RuleRegistry`, all 8 rules implemented independently, configurable thresholds
- [x] **Phase 4**: Risk Scoring & Explainability service (`RiskScorer`, `RiskAssessment`, `RuleContribution`), score bounding [0–100], risk tiers (LOW/MED/HIGH/CRIT), evidence preservation, deterministic explanation generation, 100% test pass rate (75 tests passing)
- [x] **Phase 5**: User Behaviour Profile baseline calculation, `UserBehaviourProfileService`, `BehaviourProfileCalculator`, `RuleContext` integration with Phase 3 rules (`UnusualTransactionAmountRule`, `DeviceChangeRule`, `UnusualTimeRule`, `UnusualMerchantRule`), `GET /api/users/{user_id}/behaviour-profile`, 100% test pass rate (103 tests passing)
- [x] **Phase 6**: Software-based Device Fingerprinting & Device Change Detection, User-Agent browser & OS parsing, `DeviceService`, `DeviceChangeRule` compound threat detection ("New Device + New Location"), `GET/POST /api/users/{user_id}/devices`, 100% test pass rate (131 tests passing)
- [x] **Phase 7**: Unusual Time Detection with overnight window & timezone awareness, Account Takeover (ATO) correlation engine with 5 signals, tri-state evaluation, explainable assessment, `GET /api/users/{user_id}/account-takeover-risk`, 100% test pass rate (153 tests passing)
- [x] **Phase 8**: Chronological Transaction Journey aggregation, normalized event representation, deterministic ordering, duplicate protection, missing data resilience, `GET /api/transactions/{id}/journey`, React vertical timeline component, 100% test pass rate (162 tests passing)


## 🛠 Technology Stack

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Validation & Settings**: Pydantic v2 & Pydantic Settings
- **ORM / Database**: SQLAlchemy 2.0 with SQLite (`sqlite:///./fraudshield.db`)
- **Database Migrations**: Alembic
- **Testing**: Pytest & Starlette TestClient (HTTPX)
- **Logging**: Python Standard Library `logging` with structured format

### Frontend
- **Framework**: React 19 + TypeScript
- **Tooling**: Vite
- **Styling**: Tailwind CSS v4
- **Icons**: Lucide React

---

## 📁 Project Structure

```text
fraudshield/
├── backend/
│   ├── alembic/               # Alembic database migration environment
│   │   ├── versions/          # Migration version scripts (for future models)
│   │   ├── env.py             # Alembic migration runner with Base.metadata
│   │   └── script.py.mako
│   ├── app/
│   │   ├── __init__.py        # Backend package marker
│   │   ├── config.py          # Pydantic Settings & environment parsing
│   │   ├── database.py        # SQLAlchemy engine, sessionmaker, get_db, init_db
│   │   ├── logging_config.py  # Structured standard logging configuration
│   │   ├── exceptions.py      # Centralized error handling & sanitization
│   │   ├── models/            # SQLAlchemy 2.0 ORM models (Phase 2)
│   │   ├── repositories/      # Data access layer repositories (Phase 2)
│   │   ├── fraud/             # Extensible Rule Engine (Phase 3) & Risk Scoring (Phase 4)
│   │   ├── behaviour/         # User Behaviour Profile baseline & comparison (Phase 5)
│   │   ├── routers/           # FastAPI API routers (health, behaviour, etc.)
│   │   ├── schemas/           # Pydantic request & response schemas
│   │   └── main.py            # FastAPI app, lifespan, CORS, middleware
│   ├── tests/                 # 103 Pytest unit, property, and integration tests
│   ├── alembic.ini            # Alembic config for backend directory
│   ├── requirements.txt       # Core backend dependencies
│   ├── .env.example           # Backend environment variable template
│   └── .env                   # Local backend environment file (git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Header, ConnectionStatusCard, ArchitectureCard
│   │   ├── pages/             # HomePage
│   │   ├── services/          # API service calling /health & /api
│   │   ├── types/             # TypeScript interfaces
│   │   ├── App.tsx            # Root application layout
│   │   ├── index.css          # Tailwind CSS styles
│   │   └── main.tsx           # React DOM root entry
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── .env.example           # Frontend environment variable template
│   └── .env                   # Local frontend environment file (git-ignored)
│
├── .gitignore                 # Root gitignore (.env, node_modules, .venv, *.db)
├── .env.example               # Root combined environment template
├── alembic.ini                # Root Alembic configuration
└── README.md                  # Project documentation
```

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)
```bash
APP_NAME=FraudShield
APP_ENV=development
DATABASE_URL=sqlite:///./fraudshield.db
API_PREFIX=/api
LOG_LEVEL=INFO
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

### Frontend (`frontend/.env`)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🚀 Running the Project

### 1. Backend Setup & Run

From the repository root:

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1
# On Linux/macOS: source .venv/bin/activate

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Create .env if not present
cp .env.example .env

# 4. Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **API Information**: [http://127.0.0.1:8000/api](http://127.0.0.1:8000/api)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Running Backend Tests
```bash
pytest backend/tests
```

#### Running Database Migrations (Alembic)
```bash
cd backend
alembic current
# To generate a revision in Phase 2+:
# alembic revision --autogenerate -m "create fraud tables"
# alembic upgrade head
```

---

### 2. Frontend Setup & Run

From the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend client will open at:
- [http://localhost:5173](http://localhost:5173)

The page verifies connectivity with the backend by requesting `GET /health` and displays:
- **Backend Status: Connected**
- Active Database status: `connected`
- Measured latency and response payload

---

## 🛡️ Error Handling & Logging

All errors return a consistent, standardized JSON contract:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": []
  }
}
```
Internal unhandled errors (500) log full tracebacks to stdout without leaking sensitive stack traces to clients.

Internal unhandled errors (500) log full tracebacks to stdout without leaking sensitive stack traces to clients.

---

## 🌐 Phase 9 — Fraud REST API Layer

Phase 9 exposes the entire FraudShield intelligence engine through clean, consistent, frontend-ready REST endpoints under `/api`.

### 1. Architectural Principles
- **No Duplication of Fraud Logic**: APIs act as pure orchestration and query layers, delegating to `FraudRuleEngine`, `RiskScorer`, `UserBehaviourProfileService`, `DeviceService`, `AccountTakeoverDetector`, and `TransactionJourneyService`.
- **Phase 6 Device Lifecycle Ordering**: Ingestion checks `is_known_device` *before* rules evaluate (`DeviceChangeRule`), and only registers/refreshes device telemetry *after* evaluation.
- **SQL Aggregations**: Dashboard statistics and analytics use database aggregation functions (`func.count`, `func.avg`, `case`, `group_by`) rather than pulling full tables into Python memory.
- **Explainability Preserved**: Full rule contributions, trigger flags, and compound ATO assessments are persisted and returned.

### 2. Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/transactions` | Ingest transaction, run fraud pipeline, persist results & flags, return explainable assessment |
| `GET` | `/api/transactions` | Paginated list of transactions with status, risk, date, and user filters |
| `GET` | `/api/transactions/{id}` | Detailed forensic view of a transaction, triggered rules, and flags |
| `PATCH` | `/api/transactions/{id}/status` | Transition review status (`PENDING_REVIEW`, `REVIEWED`, `CLEARED`, `ESCALATED`) |
| `GET` | `/api/users/{id}/profile` | Retrieve behavioural baseline and transaction profile |
| `GET` | `/api/users/{id}/journey` | Retrieve user-level chronological activity timeline |
| `GET` | `/api/transactions/{id}/journey` | Retrieve transaction-centric journey timeline (Phase 8 preserved) |
| `GET` | `/api/dashboard/stats` | Real-time aggregate reviewer statistics (counts, averages, queues) |
| `GET` | `/api/analytics/fraud` | Fraud distributions (risk tiers, rule trigger counts, review status, daily trend) |
| `GET` | `/api/rules` | List all registered fraud rules directly from `RuleRegistry` |
| `GET` | `/api/rules/performance` | Rule evaluation count, trigger count, trigger rate, and score impact |

---

## 🖥️ Phase 10 — React Reviewer Console

Phase 10 provides the primary user interface for fraud analysts and reviewers. It is built in React 19 + TypeScript + Tailwind CSS and interacts with the Phase 9 REST API layer without duplicating backend fraud logic.

### 1. Architectural Highlights
- **Real-Time KPI Dashboard**: Displays 7 core operational metrics fetched directly from `GET /api/dashboard/stats`: Total Transactions, Flagged, High Risk, Critical, Pending Review, Reviewed, and Cleared.
- **Accessible Visual Hierarchy**: Risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) use prominent badges combining semantic iconography, distinctive border/surface colors, and accessible text labels (never relying on color alone).
- **Interactive Review Queue Table**: Displays 8 essential columns: Transaction ID, User ID, Formatted Currency Amount, Geolocation, Risk Score, Risk Level badge, Review Status badge, and Localized Timestamp.
- **Backend-Driven Filtering & Pagination**: Paginated via `GET /api/transactions` with query-driven filtering (Risk Tier, Review Status, User ID search) and pagination controls (`Previous`, page indicator, `Next`).
- **Quick Status Workflow**: Exposes atomic status updates via `PATCH /api/transactions/{id}/status` with in-flight spinner feedback, immediate UI refresh of both the table and KPI cards, and error handling.
- **Extensible Routing**: React Router v7 routes (`/dashboard`, `/transactions/:id`, `/journey`, `/system`) with clickable transaction rows that smoothly navigate to transaction detail shells.

---

## 🔍 Phase 11 — "Why Flagged?" Investigation UI

Phase 11 introduces the deep forensic investigation workspace (`/transactions/:id`) for FraudShield. Reviewers transitioning from the Phase 10 queue immediately understand the complete context and explainable story behind any flagged transaction.

### 1. Key Principles
- **Backend as Single Source of Truth**: The React UI performs zero fraud score calculations, rule evaluations, or risk determinations. It renders backend assessments (`risk.score`, `rule_results`, `evidence`, `account_takeover`).
- **Explainability Storytelling**: Transforms isolated heuristics into an intuitive investigation story:
  1. **Top Banner**: Reference, user ID, formatted currency, geolocation, and inline review status updater.
  2. **"Why Flagged?" Section**: Prominent visual gauge (`/ 100`), `RiskBadge` with CRITICAL emphasis, and human-readable explanation summary.
  3. **Triggered Rules Accordion**: Score contributions (`+25`, `+30`), rule names, human-readable reasons, and expandable evidence blocks.
  4. **Safe Evidence Renderer**: Dynamically formats strings, numbers, currencies, ratios, arrays, and nested structures with an optional raw JSON technical view.
  5. **User Behaviour Baseline**: Displays normal transaction ranges, frequency, active hours, and highlights anomalies (e.g. 12× user average, unrecognized city, off-hours activity).
  6. **Device Intelligence**: Displays device ID, browser, OS, network IP, detection history, and visual `NEW DEVICE ⚠️` vs `KNOWN DEVICE` classification.
  7. **Account Takeover Assessment**: Independent ATO threat level and 5-signal correlation checklist (New Device, Unusual Time, New Location, Failed Login, Amount Surge).
  8. **Chronological Journey**: Directly embeds the Phase 8 `TransactionJourney` timeline showing preceding and succeeding events.
- **Decoupled Failure Tolerance**: Secondary requests (e.g., user behaviour profile or journey) do not block or break the main transaction investigation screen.

---

## 🧪 Phase Acceptance Checklist

- [x] **Phase 1**: FastAPI skeleton, SQLite connectivity, Alembic config, health checks
- [x] **Phase 2**: Relational ORM models (User, Device, Transaction, FraudRuleResult, FraudFlag, Review, etc.)
- [x] **Phase 3**: Modular Fraud Rule Engine with 8 independent heuristic rules & context builder
- [x] **Phase 4**: Explainable Risk Scoring, categorized Risk Levels, bounded 0-100 scores
- [x] **Phase 5**: User Behaviour Profiling with rolling statistics and deviation detection
- [x] **Phase 6**: Software-based Device Fingerprinting & lifecycle-ordered device change detection
- [x] **Phase 7**: Temporal anomaly detection & compound Account Takeover (ATO) correlation
- [x] **Phase 8**: Chronological Transaction Journey timeline aggregation
- [x] **Phase 9 — Fraud APIs**: Complete REST API orchestration layer (175/175 Pytest tests passing)
- [x] **Phase 10 — React Reviewer Console**:
  - [x] Reviewer Dashboard with 7 core KPI stat cards from `GET /api/dashboard/stats`
  - [x] No hardcoded numbers or fake statistics; real data source of truth
  - [x] Transaction Table displaying all 8 columns: ID, User, Amount, Location, Score, Level, Status, Time
  - [x] Accessible `RiskBadge` with text labels and semantic styling
  - [x] Human-readable `StatusBadge` covering all supported review/transaction statuses
  - [x] Reusable currency and localized timestamp formatters (INR, USD, ISO-8601)
  - [x] Backend-driven pagination and multi-parameter filtering
  - [x] Skeletons, empty states, and retryable error states
  - [x] Row interaction navigating to `/transactions/:id` detail shell
  - [x] Quick status update action with in-place feedback and dashboard refresh
  - [x] 30/30 Vitest frontend tests passing across 6 test suites
  - [x] 175/175 Pytest backend tests passing with 0 regressions
- [x] **Phase 11 — "Why Flagged?" Investigation UI**:
  - [x] Main route `/transactions/:id` connected to transaction table row click
  - [x] Prominent investigation header with amount, user, location, timestamp, and review status
  - [x] Visual risk score gauge (`/ 100`) and prominent severity badge (CRITICAL, HIGH, MEDIUM, LOW)
  - [x] "Why Flagged?" core narrative explaining detection results in plain English
  - [x] Triggered rules breakdown displaying rule names, score contributions (`+25`, `+30`, `+35`), and reasons
  - [x] Safe, generic evidence renderer formatting numbers, strings, booleans, arrays, and nested objects cleanly
  - [x] Expandable/collapsible rule cards with "Expand all" / "Collapse all" controls and raw JSON toggle
  - [x] User Behaviour Profile section with baseline comparison chips highlighting deviations (ratio, location, hours)
  - [x] Device Information section showing client environment, IP, timestamps, and `NEW DEVICE ⚠️` warning badge
  - [x] Account Takeover (ATO) card with compound threat level and 5-signal checklist
  - [x] Embedded Phase 8 `TransactionJourney` component displaying complete chronological context
  - [x] Decoupled loading states, skeletons, and graceful fallback with retry for profile
  - [x] Inline status transition action with backend persistence via `PATCH /api/transactions/{id}/status`
  - [x] 48/48 Vitest frontend tests passing across 13 test suites
  - [x] 175/175 Pytest backend tests passing with 0 regressions

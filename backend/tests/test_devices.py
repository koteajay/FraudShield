"""Comprehensive Unit and Integration Tests for Phase 6 Device Fingerprinting & Device Change Detection."""

import pytest
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User
from app.models.device import Device
from app.devices.metadata import (
    DeviceMetadata,
    extract_device_metadata,
    parse_browser,
    parse_operating_system,
    parse_device_type,
)
from app.devices.service import DeviceService
from app.fraud.context import RuleContext
from app.fraud.rules.device_change import DeviceChangeRule
from app.behaviour.models import UserBehaviourProfile, ProfileStatus


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides isolated in-memory SQLite database session."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(name="client")
def fixture_client(db_session: Session):
    """FastAPI test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. BROWSER PARSING TESTS
# ---------------------------------------------------------------------------

def test_parse_browser_chrome():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    assert parse_browser(ua) == "Chrome"


def test_parse_browser_firefox():
    ua = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    assert parse_browser(ua) == "Firefox"


def test_parse_browser_safari():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15"
    assert parse_browser(ua) == "Safari"


def test_parse_browser_edge():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.92"
    assert parse_browser(ua) == "Edge"


def test_parse_browser_opera():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/107.0.0.0"
    assert parse_browser(ua) == "Opera"


def test_parse_browser_unknown_and_empty():
    assert parse_browser(None) == "Unknown"
    assert parse_browser("") == "Unknown"
    assert parse_browser("curl/7.68.0") == "Unknown"


# ---------------------------------------------------------------------------
# 2. OPERATING SYSTEM PARSING TESTS
# ---------------------------------------------------------------------------

def test_parse_os_windows():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0"
    assert parse_operating_system(ua) == "Windows"


def test_parse_os_macos():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0"
    assert parse_operating_system(ua) == "macOS"


def test_parse_os_linux():
    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0"
    assert parse_operating_system(ua) == "Linux"


def test_parse_os_android():
    ua = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Mobile Safari/537.36"
    assert parse_operating_system(ua) == "Android"


def test_parse_os_ios():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"
    assert parse_operating_system(ua) == "iOS"


def test_parse_os_unknown_and_empty():
    assert parse_operating_system(None) == "Unknown"
    assert parse_operating_system("") == "Unknown"
    assert parse_operating_system("python-requests/2.31.0") == "Unknown"


# ---------------------------------------------------------------------------
# 3. DEVICE TYPE PARSING TESTS
# ---------------------------------------------------------------------------

def test_parse_device_type():
    assert parse_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)") == "mobile"
    assert parse_device_type("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)") == "tablet"
    assert parse_device_type("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") == "desktop"
    assert parse_device_type("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)") == "desktop"
    assert parse_device_type("Custom-Bot/1.0") == "unknown"


# ---------------------------------------------------------------------------
# 4. METADATA EXTRACTION TESTS
# ---------------------------------------------------------------------------

def test_extract_device_metadata_with_explicit_id():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
    meta = extract_device_metadata(user_agent=ua, ip_address="192.168.1.100", device_id="DEV-CLIENT-123")
    assert meta.device_id == "DEV-CLIENT-123"
    assert meta.browser == "Chrome"
    assert meta.operating_system == "Windows"
    assert meta.ip_address == "192.168.1.100"
    assert meta.device_type == "desktop"


def test_extract_device_metadata_generates_fallback_uuid():
    meta = extract_device_metadata(user_agent="Unknown", ip_address=None, device_id=None)
    assert meta.device_id is not None
    assert len(meta.device_id) > 10
    assert meta.browser == "Unknown"


# ---------------------------------------------------------------------------
# 5. DEVICE MODEL INITIALIZATION TESTS
# ---------------------------------------------------------------------------

def test_device_model_defaults():
    dev = Device(user_id="U1", device_id="DEV-TEST-001")
    assert dev.device_id == "DEV-TEST-001"
    assert dev.fingerprint == "DEV-TEST-001"
    assert dev.device_type == "unknown"
    assert dev.is_trusted is False


def test_device_model_fingerprint_synchronization():
    dev = Device(user_id="U1", fingerprint="fp_hash_999")
    assert dev.fingerprint == "fp_hash_999"
    assert dev.device_id == "fp_hash_999"


# ---------------------------------------------------------------------------
# 6. DEVICE SERVICE: REGISTRATION & FIRST/LAST SEEN TIMESTAMPS
# ---------------------------------------------------------------------------

def test_register_device_first_and_last_seen(db_session: Session):
    user = User(id="user_dev_1", username="dev_user", email="dev1@example.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    service = DeviceService(db_session)
    meta = extract_device_metadata(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
        ip_address="127.0.0.1",
        device_id="DEV-REG-001",
    )
    device = service.register_device(user.id, meta)

    assert device.user_id == user.id
    assert device.device_id == "DEV-REG-001"
    assert device.browser == "Chrome"
    assert device.operating_system == "Windows"
    assert device.first_seen_at is not None
    assert device.last_seen_at is not None
    assert device.first_seen_at == device.last_seen_at


def test_update_last_seen_preserves_first_seen(db_session: Session):
    user = User(id="user_dev_2", username="dev_user_2", email="dev2@example.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    service = DeviceService(db_session)
    meta = extract_device_metadata(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
        ip_address="127.0.0.1",
        device_id="DEV-REG-002",
    )
    device = service.register_device(user.id, meta)
    initial_first_seen = device.first_seen_at
    initial_last_seen = device.last_seen_at

    # Simulate subsequent activity
    time.sleep(0.01)
    updated = service.update_last_seen(device, ip_address="10.0.0.1")

    assert updated.first_seen_at == initial_first_seen
    assert updated.last_seen_at >= initial_last_seen
    assert updated.ip_address == "10.0.0.1"


# ---------------------------------------------------------------------------
# 7. KNOWN VS NEW DEVICE DETECTION
# ---------------------------------------------------------------------------

def test_is_known_device_detection(db_session: Session):
    user1 = User(id="u_alice", username="alice", email="alice@example.com", hashed_password="p", role=UserRole.USER)
    user2 = User(id="u_bob", username="bob", email="bob@example.com", hashed_password="p", role=UserRole.USER)
    db_session.add_all([user1, user2])
    db_session.commit()

    service = DeviceService(db_session)
    meta = extract_device_metadata(user_agent="Chrome", device_id="ALICE-LAPTOP")
    service.register_device(user1.id, meta)

    # Alice's device is known to Alice
    assert service.is_known_device(user1.id, "ALICE-LAPTOP") is True
    # Alice's device is NOT known to Bob
    assert service.is_known_device(user2.id, "ALICE-LAPTOP") is False
    # Unknown device for Alice
    assert service.is_known_device(user1.id, "ALICE-NEW-PHONE") is False


def test_get_or_create_device_flow(db_session: Session):
    user = User(id="u_charlie", username="charlie", email="charlie@example.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    service = DeviceService(db_session)
    meta = extract_device_metadata(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/605.1.15",
        ip_address="192.168.1.50",
        device_id="CHARLIE-MACBOOK",
    )

    # First encounter -> New device
    dev1, is_new1 = service.get_or_create_device(user.id, meta)
    assert is_new1 is True
    assert dev1.device_id == "CHARLIE-MACBOOK"

    # Second encounter -> Known device refreshed
    dev2, is_new2 = service.get_or_create_device(user.id, meta)
    assert is_new2 is False
    assert dev2.id == dev1.id
    assert dev2.device_id == "CHARLIE-MACBOOK"


# ---------------------------------------------------------------------------
# 8. INTEGRATION WITH DEVICE CHANGE RULE
# ---------------------------------------------------------------------------

def test_device_change_rule_known_device():
    rule = DeviceChangeRule()
    known = [
        Device(id="dev_1", device_id="DEV-PHONE-1", fingerprint="DEV-PHONE-1"),
        Device(id="dev_2", device_id="DEV-LAPTOP-2", fingerprint="DEV-LAPTOP-2"),
    ]
    curr_dev = Device(id="dev_1", device_id="DEV-PHONE-1", fingerprint="DEV-PHONE-1")
    ctx = RuleContext(
        current_transaction={"id": "tx1", "device_id": "DEV-PHONE-1"},
        known_devices=known,
        current_device=curr_dev,
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert result.score_contribution == 0.0
    assert result.evidence["is_new_device"] is False


def test_device_change_rule_new_device():
    rule = DeviceChangeRule()
    known = [Device(id="dev_1", device_id="DEV-PHONE-1", fingerprint="DEV-PHONE-1")]
    curr_dev = Device(id="dev_new", device_id="DEV-ATTACKER-99", fingerprint="DEV-ATTACKER-99")
    ctx = RuleContext(
        current_transaction={"id": "tx2", "device_id": "DEV-ATTACKER-99"},
        known_devices=known,
        current_device=curr_dev,
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.score_contribution == 15.0
    assert result.evidence["is_new_device"] is True
    assert result.evidence["new_device_new_location"] is False
    assert "Transaction originated from an unfamiliar device" in result.reason


def test_device_change_rule_new_device_plus_new_location():
    rule = DeviceChangeRule()
    profile = UserBehaviourProfile(
        user_id="U1",
        profile_status=ProfileStatus.ESTABLISHED,
        known_devices=1,
        known_device_ids=["DEV-PHONE-1"],
        known_locations=["Hyderabad, IN"],
        profile_transaction_count=20,
    )
    curr_dev = Device(id="dev_new", device_id="DEV-ATTACKER-99", fingerprint="DEV-ATTACKER-99")
    ctx = RuleContext(
        current_transaction={
            "id": "tx3",
            "device_id": "DEV-ATTACKER-99",
            "city": "Moscow",
            "country": "RU",
        },
        known_devices=[Device(id="dev_1", device_id="DEV-PHONE-1")],
        current_device=curr_dev,
        user_profile=profile,
    )
    result = rule.evaluate(ctx)
    assert result.triggered is True
    assert result.evidence["is_new_device"] is True
    assert result.evidence["new_device_new_location"] is True
    assert "combined with an unrecognized location" in result.reason


def test_device_change_rule_initial_user_no_devices():
    rule = DeviceChangeRule()
    ctx = RuleContext(
        current_transaction={"id": "tx4", "device_id": "FIRST-DEV"},
        known_devices=[],
        current_device=Device(id="dev_first", device_id="FIRST-DEV"),
    )
    result = rule.evaluate(ctx)
    assert result.triggered is False
    assert "Initial transaction for user; no prior baseline" in result.reason


# ---------------------------------------------------------------------------
# 9. API ENDPOINTS TESTS
# ---------------------------------------------------------------------------

def test_api_list_user_devices(client: TestClient, db_session: Session):
    user = User(id="api_u_1", username="api_u1", email="u1@test.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    service = DeviceService(db_session)
    service.register_device(user.id, extract_device_metadata(user_agent="Chrome", device_id="DEV-A"))
    service.register_device(user.id, extract_device_metadata(user_agent="Firefox", device_id="DEV-B"))

    response = client.get(f"/api/users/{user.id}/devices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    device_ids = {d["device_id"] for d in data}
    assert "DEV-A" in device_ids
    assert "DEV-B" in device_ids


def test_api_register_and_refresh_device(client: TestClient, db_session: Session):
    user = User(id="api_u_2", username="api_u2", email="u2@test.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    # 1. Register new device
    payload = {
        "device_id": "CLIENT-APP-12345",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0",
        "ip_address": "203.0.113.195",
    }
    res1 = client.post(f"/api/users/{user.id}/devices", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_new_device"] is True
    assert data1["is_known"] is False
    assert data1["device"]["browser"] == "Chrome"
    assert data1["device"]["operating_system"] == "Windows"

    # 2. Subsequent call refreshes same device
    res2 = client.post(f"/api/users/{user.id}/devices", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_new_device"] is False
    assert data2["is_known"] is True
    assert data2["device"]["id"] == data1["device"]["id"]


def test_api_get_device_detail(client: TestClient, db_session: Session):
    user = User(id="api_u_3", username="api_u3", email="u3@test.com", hashed_password="p", role=UserRole.USER)
    db_session.add(user)
    db_session.commit()

    service = DeviceService(db_session)
    dev = service.register_device(user.id, extract_device_metadata(user_agent="Safari", device_id="SPECIFIC-DEV"))

    # Found
    res = client.get(f"/api/users/{user.id}/devices/SPECIFIC-DEV")
    assert res.status_code == 200
    assert res.json()["device_id"] == "SPECIFIC-DEV"

    # Not found
    res_404 = client.get(f"/api/users/{user.id}/devices/NON-EXISTENT-DEVICE")
    assert res_404.status_code == 404

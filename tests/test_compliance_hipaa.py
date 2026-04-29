"""Tests for HIPAA compliance profiles and audit log."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import audit_log


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so clinical recognizers are registered."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_audit_log():
    """Clear audit log before each test for isolation."""
    audit_log.clear()


def test_hipaa_safe_harbor_basic(client):
    """Safe Harbor should anonymize email and return framework == 'hipaa-safe-harbor'."""
    response = client.post(
        "/compliance/hipaa/safe-harbor",
        json={
            "text": "John Smith's SSN is 078-05-1120 and email is john@example.com, IP 192.168.1.1.",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "hipaa-safe-harbor"
    assert "john@example.com" not in data["text"]


def test_hipaa_safe_harbor_risk_score(client):
    """Safe Harbor response should include a valid risk_score and risk_level."""
    response = client.post(
        "/compliance/hipaa/safe-harbor",
        json={
            "text": "Patient Jane Doe, SSN 078-05-1120.",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["risk_score"], float)
    assert data["risk_level"] in ("low", "medium", "high")


def test_hipaa_expert_determination_high_risk(client):
    """Text with multiple direct identifiers should yield medium or high risk."""
    response = client.post(
        "/compliance/hipaa/expert-determination",
        json={
            "text": (
                "Patient Alice Johnson, SSN 078-05-1120, email alice@hospital.com, "
                "phone 555-867-5309, credit card 4111-1111-1111-1111."
            ),
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ("medium", "high")


def test_hipaa_expert_determination_low_risk(client):
    """Text without PII should yield low risk."""
    response = client.post(
        "/compliance/hipaa/expert-determination",
        json={
            "text": "The weather today is sunny with a high of 25 degrees.",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "low"


def test_audit_log_populated(client):
    """After a compliance operation, audit log should have at least one entry."""
    client.post(
        "/compliance/hipaa/safe-harbor",
        json={"text": "Patient Bob, SSN 078-05-1120.", "language": "en"},
    )
    response = client.get("/compliance/audit-log?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) >= 1


def test_audit_log_filter_by_framework(client):
    """Audit log filtered by framework should only return matching entries."""
    # Trigger a safe-harbor operation
    client.post(
        "/compliance/hipaa/safe-harbor",
        json={"text": "Patient Carol, SSN 078-05-1120.", "language": "en"},
    )
    response = client.get("/compliance/audit-log?framework=hipaa-safe-harbor")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for entry in data["entries"]:
        assert entry["framework"] == "hipaa-safe-harbor"

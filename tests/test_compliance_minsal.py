"""Tests for MINSAL Chile / Ley 19.628 compliance profile."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so clinical recognizers are registered."""
    with TestClient(app) as c:
        yield c


def test_minsal_anonymize_rut(client):
    """RUT chileno should be detected and replaced; framework should be 'minsal'."""
    response = client.post(
        "/compliance/minsal",
        json={
            "text": "El paciente con RUT 12.345.678-9 fue atendido hoy.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "minsal"
    assert "12.345.678-9" not in data["text"]


def test_minsal_anonymize_fonasa(client):
    """FONASA and clinical record numbers should be anonymized."""
    response = client.post(
        "/compliance/minsal",
        json={
            "text": "Previsión: FONASA-12345678. Ficha clínica: HC-000456.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "FONASA-12345678" not in data["text"]
    assert "HC-000456" not in data["text"]


def test_minsal_phone(client):
    """Chilean phone numbers should be masked."""
    response = client.post(
        "/compliance/minsal",
        json={
            "text": "Contactar al paciente en su celular +56912345678.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # The phone should have been masked (not appear in full)
    assert "+56912345678" not in data["text"]


def test_minsal_frameworks_list(client):
    """GET /compliance/frameworks should include minsal, hipaa-safe-harbor and iso-25237."""
    response = client.get("/compliance/frameworks")
    assert response.status_code == 200
    ids = [f["id"] for f in response.json()]
    assert "minsal" in ids
    assert "hipaa-safe-harbor" in ids
    assert "iso-25237" in ids


def test_minsal_risk_score_present(client):
    """MINSAL response should include risk_score and risk_level."""
    response = client.post(
        "/compliance/minsal",
        json={
            "text": "Paciente: Juan Pérez, RUT 12.345.678-9.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] is not None
    assert isinstance(data["risk_score"], float)
    assert data["risk_level"] in ("low", "medium", "high")

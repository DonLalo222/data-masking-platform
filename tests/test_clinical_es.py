"""Tests for Spanish clinical recognizers (ISO/CIE-10/HL7 support)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so clinical recognizers are registered."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# DNI
# ---------------------------------------------------------------------------

def test_detect_dni(client):
    response = client.post(
        "/analyze",
        json={
            "text": "El paciente con DNI 12345678Z fue ingresado el lunes.",
            "language": "es",
            "entities": ["ES_DNI"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_DNI" in types


def test_detect_dni_value(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Documento: 87654321R",
            "language": "es",
            "entities": ["ES_DNI"],
        },
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(e["entity_type"] == "ES_DNI" and e["text"] == "87654321R" for e in entities)


# ---------------------------------------------------------------------------
# NIE
# ---------------------------------------------------------------------------

def test_detect_nie(client):
    response = client.post(
        "/analyze",
        json={
            "text": "La paciente extranjera con NIE X1234567L acudió a urgencias.",
            "language": "es",
            "entities": ["ES_NIE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_NIE" in types


def test_detect_nie_z_prefix(client):
    response = client.post(
        "/analyze",
        json={
            "text": "NIE del paciente: Z9876543B",
            "language": "es",
            "entities": ["ES_NIE"],
        },
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(e["entity_type"] == "ES_NIE" and e["text"] == "Z9876543B" for e in entities)


# ---------------------------------------------------------------------------
# Tarjeta sanitaria (CIP / SNS)
# ---------------------------------------------------------------------------

def test_detect_tarjeta_sanitaria(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Tarjeta sanitaria del paciente: MDRP12345678.",
            "language": "es",
            "entities": ["ES_TARJETA_SANITARIA"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_TARJETA_SANITARIA" in types


def test_detect_tarjeta_sanitaria_value(client):
    response = client.post(
        "/analyze",
        json={
            "text": "CIP: ABCD12345678",
            "language": "es",
            "entities": ["ES_TARJETA_SANITARIA"],
        },
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(
        e["entity_type"] == "ES_TARJETA_SANITARIA" and e["text"] == "ABCD12345678"
        for e in entities
    )


# ---------------------------------------------------------------------------
# NUHSA
# ---------------------------------------------------------------------------

def test_detect_nuhsa(client):
    response = client.post(
        "/analyze",
        json={
            "text": "NUHSA del paciente: AN0123456789.",
            "language": "es",
            "entities": ["ES_NUHSA"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_NUHSA" in types


# ---------------------------------------------------------------------------
# CIE-10 codes
# ---------------------------------------------------------------------------

def test_detect_cie10(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Diagnóstico principal: J18.9 (Neumonía no especificada).",
            "language": "es",
            "entities": ["ES_CIE10_CODE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_CIE10_CODE" in types


def test_detect_cie10_without_decimal(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Código CIE-10: A15",
            "language": "es",
            "entities": ["ES_CIE10_CODE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_CIE10_CODE" in types


# ---------------------------------------------------------------------------
# Spanish phone numbers
# ---------------------------------------------------------------------------

def test_detect_phone_es(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Puede contactar al paciente en el teléfono 612345678.",
            "language": "es",
            "entities": ["ES_PHONE_NUMBER"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_PHONE_NUMBER" in types


def test_detect_phone_es_with_prefix(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Teléfono de contacto: +34912345678",
            "language": "es",
            "entities": ["ES_PHONE_NUMBER"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_PHONE_NUMBER" in types


# ---------------------------------------------------------------------------
# Spanish postal codes
# ---------------------------------------------------------------------------

def test_detect_postal_code(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Dirección del paciente: Calle Mayor 5, código postal 28001, Madrid.",
            "language": "es",
            "entities": ["ES_POSTAL_CODE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "ES_POSTAL_CODE" in types


# ---------------------------------------------------------------------------
# PERSON entity in Spanish
# ---------------------------------------------------------------------------

def test_person_in_spanish(client):
    response = client.post(
        "/analyze",
        json={
            "text": "La paciente María García fue dada de alta.",
            "language": "es",
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "PERSON" in types


# ---------------------------------------------------------------------------
# Idempotency: calling register twice must not raise
# ---------------------------------------------------------------------------

def test_register_idempotent(client):
    from app.services.analyzer import get_engine
    from app.services.clinical_recognizers_es import register_clinical_recognizers_es

    registry = get_engine().registry
    size_before = len(registry.recognizers)
    register_clinical_recognizers_es()
    size_after = len(registry.recognizers)
    # A second registration must not add duplicate entries
    assert size_after == size_before


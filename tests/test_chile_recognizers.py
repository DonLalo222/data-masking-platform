"""Tests for Chilean identification document recognizers."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so Chilean recognizers are registered."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# CL_RUN — RUN/RUT chileno
# ---------------------------------------------------------------------------

def test_detect_run_with_dots(client):
    response = client.post(
        "/analyze",
        json={
            "text": "El RUT del paciente es 12.345.678-9",
            "language": "es",
            "entities": ["CL_RUN"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUN" in types


def test_detect_run_without_dots(client):
    response = client.post(
        "/analyze",
        json={
            "text": "RUN: 12345678-9",
            "language": "es",
            "entities": ["CL_RUN"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUN" in types


def test_detect_run_with_k_verifier(client):
    response = client.post(
        "/analyze",
        json={
            "text": "RUT 9.876.543-K",
            "language": "es",
            "entities": ["CL_RUN"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUN" in types


def test_run_with_dots_value(client):
    response = client.post(
        "/analyze",
        json={
            "text": "rut del paciente: 12.345.678-9",
            "language": "es",
            "entities": ["CL_RUN"],
        },
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert any(e["entity_type"] == "CL_RUN" and e["text"] == "12.345.678-9" for e in entities)


def test_no_false_positive_plain_number(client):
    """A plain number without context and without the RUT dash-verifier format
    should NOT be detected as a CL_RUN."""
    response = client.post(
        "/analyze",
        json={
            "text": "El código del producto es 12345678",
            "language": "es",
            "entities": ["CL_RUN"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUN" not in types


# ---------------------------------------------------------------------------
# CL_PASAPORTE
# ---------------------------------------------------------------------------

def test_detect_pasaporte(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Pasaporte A1234567",
            "language": "es",
            "entities": ["CL_PASAPORTE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_PASAPORTE" in types


def test_detect_pasaporte_two_letters(client):
    response = client.post(
        "/analyze",
        json={
            "text": "número de pasaporte: AB123456",
            "language": "es",
            "entities": ["CL_PASAPORTE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_PASAPORTE" in types


# ---------------------------------------------------------------------------
# CL_PHONE — teléfonos chilenos
# ---------------------------------------------------------------------------

def test_detect_phone_with_plus56(client):
    response = client.post(
        "/analyze",
        json={
            "text": "su teléfono es +56 9 1234 5678",
            "language": "es",
            "entities": ["CL_PHONE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_PHONE" in types


def test_detect_phone_local(client):
    response = client.post(
        "/analyze",
        json={
            "text": "celular: 912345678",
            "language": "es",
            "entities": ["CL_PHONE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_PHONE" in types


# ---------------------------------------------------------------------------
# Idempotency: calling register twice must not raise
# ---------------------------------------------------------------------------

def test_register_idempotent(client):
    from app.services.analyzer import get_engine
    from app.services.chile_recognizers import register_chile_recognizers

    registry = get_engine().registry
    size_before = len(registry.recognizers)
    register_chile_recognizers()
    size_after = len(registry.recognizers)
    # A second registration must not add duplicate entries
    assert size_after == size_before
    # Chilean recognizers must still be present after re-registration
    names = [r.name for r in registry.recognizers]
    assert "ClRunWithDotsRecognizer" in names

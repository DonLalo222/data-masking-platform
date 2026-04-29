"""Tests for Chilean clinical recognizers (MINSAL / Ley 19.628 / Ley 20.584)."""

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
# CL_RUT — with dots
# ---------------------------------------------------------------------------

def test_detect_rut_with_dots(client):
    response = client.post(
        "/analyze",
        json={
            "text": "El RUT del paciente es 12.345.678-9",
            "language": "es",
            "entities": ["CL_RUT"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUT" in types


# ---------------------------------------------------------------------------
# CL_RUT — without dots
# ---------------------------------------------------------------------------

def test_detect_rut_without_dots(client):
    response = client.post(
        "/analyze",
        json={
            "text": "RUN: 12345678-9",
            "language": "es",
            "entities": ["CL_RUT"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUT" in types


# ---------------------------------------------------------------------------
# CL_RUT — with K check digit
# ---------------------------------------------------------------------------

def test_detect_rut_with_k(client):
    response = client.post(
        "/analyze",
        json={
            "text": "RUT 9.876.543-K",
            "language": "es",
            "entities": ["CL_RUT"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_RUT" in types


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


# ---------------------------------------------------------------------------
# CL_CEDULA_EXTRANJERIA
# ---------------------------------------------------------------------------

def test_detect_cedula_extranjeria(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Cédula de extranjería PE1234567",
            "language": "es",
            "entities": ["CL_CEDULA_EXTRANJERIA"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_CEDULA_EXTRANJERIA" in types


# ---------------------------------------------------------------------------
# CL_FICHA_CLINICA
# ---------------------------------------------------------------------------

def test_detect_ficha_clinica(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Ficha clínica FC-12345",
            "language": "es",
            "entities": ["CL_FICHA_CLINICA"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_FICHA_CLINICA" in types


# ---------------------------------------------------------------------------
# CL_FONASA_ISAPRE — deny_list
# ---------------------------------------------------------------------------

def test_detect_fonasa_isapre(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Previsión: FONASA",
            "language": "es",
            "entities": ["CL_FONASA_ISAPRE"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_FONASA_ISAPRE" in types


# ---------------------------------------------------------------------------
# CL_REGION — deny_list
# ---------------------------------------------------------------------------

def test_detect_region(client):
    response = client.post(
        "/analyze",
        json={
            "text": "Región Metropolitana",
            "language": "es",
            "entities": ["CL_REGION"],
        },
    )
    assert response.status_code == 200
    types = [e["entity_type"] for e in response.json()["entities"]]
    assert "CL_REGION" in types


# ---------------------------------------------------------------------------
# Idempotency: calling register twice must not duplicate recognizers
# ---------------------------------------------------------------------------

def test_register_idempotent(client):
    from app.services.analyzer import get_engine
    from app.services.clinical_recognizers_cl import register_clinical_recognizers_cl

    registry = get_engine().registry
    size_before = len(registry.recognizers)
    register_clinical_recognizers_cl()
    size_after = len(registry.recognizers)
    # A second registration must not add duplicate entries
    assert size_after == size_before

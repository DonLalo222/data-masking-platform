"""Tests for ISO 25237 pseudonymization endpoints."""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so clinical recognizers are registered."""
    with TestClient(app) as c:
        yield c


def test_pseudonymize_basic(client):
    """Email should not appear in pseudonymized text; pseudonym_map should not be empty."""
    response = client.post(
        "/compliance/iso25237/pseudonymize",
        json={
            "text": "Contact me at alice@example.com for details.",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "alice@example.com" not in data["text"]
    assert len(data["pseudonym_map"]) > 0


def test_pseudonymize_deterministic(client):
    """Same input with same key should produce identical pseudonymized output."""
    payload = {
        "text": "Contact me at alice@example.com for details.",
        "language": "en",
        "pseudonym_key": "test-deterministic-key-32bytes!!",
    }
    response1 = client.post("/compliance/iso25237/pseudonymize", json=payload)
    response2 = client.post("/compliance/iso25237/pseudonymize", json=payload)
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json()["text"] == response2.json()["text"]


def test_pseudonymize_token_format(client):
    """Pseudonym tokens should match the pattern [ENTITY_TYPE_xxxxxx]."""
    response = client.post(
        "/compliance/iso25237/pseudonymize",
        json={
            "text": "My email is bob@example.com.",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Each token in pseudonym_map should follow [ENTITY_TYPE_base64url] format
    token_pattern = re.compile(r"^\[[A-Z_]+_[A-Za-z0-9_-]+\]$")
    for token in data["pseudonym_map"].keys():
        assert token_pattern.match(token), f"Token '{token}' does not match expected format"


def test_depseudonymize_roundtrip(client):
    """Pseudonymize then depseudonymize should restore the original identifier."""
    original_text = "Patient email: carol@hospital.org"
    key = "roundtrip-test-key-32bytes!!!!!!"

    # Pseudonymize
    pseudo_resp = client.post(
        "/compliance/iso25237/pseudonymize",
        json={"text": original_text, "language": "en", "pseudonym_key": key},
    )
    assert pseudo_resp.status_code == 200
    pseudo_data = pseudo_resp.json()

    # Depseudonymize
    depseudo_resp = client.post(
        "/compliance/iso25237/depseudonymize",
        json={
            "pseudonymized_text": pseudo_data["text"],
            "pseudonym_map": pseudo_data["pseudonym_map"],
        },
    )
    assert depseudo_resp.status_code == 200
    restored = depseudo_resp.json()["text"]
    assert "carol@hospital.org" in restored


def test_pseudonymize_custom_key(client):
    """Using a custom key should produce different tokens than the default key."""
    text = "Contact dave@example.com for info."
    language = "en"

    response_default = client.post(
        "/compliance/iso25237/pseudonymize",
        json={"text": text, "language": language},
    )
    response_custom = client.post(
        "/compliance/iso25237/pseudonymize",
        json={"text": text, "language": language, "pseudonym_key": "custom-key-totally-different!"},
    )

    assert response_default.status_code == 200
    assert response_custom.status_code == 200

    tokens_default = list(response_default.json()["pseudonym_map"].keys())
    tokens_custom = list(response_custom.json()["pseudonym_map"].keys())

    # Tokens generated with different keys must differ
    assert tokens_default != tokens_custom

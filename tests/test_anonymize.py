from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_anonymize_basic():
    response = client.post(
        "/anonymize",
        json={"text": "My name is John Smith", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "items" in data
    assert "John Smith" not in data["text"]


def test_anonymize_replace_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "Contact John at john@example.com",
            "language": "en",
            "operators": {
                "EMAIL_ADDRESS": {"type": "replace", "params": {"new_value": "[EMAIL]"}},
                "PERSON": {"type": "replace", "params": {"new_value": "[PERSON]"}},
            },
        },
    )
    assert response.status_code == 200
    text = response.json()["text"]
    assert "john@example.com" not in text
    assert "[EMAIL]" in text


def test_anonymize_redact_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "Delete my email: user@example.com",
            "language": "en",
            "operators": {"EMAIL_ADDRESS": {"type": "redact"}},
        },
    )
    assert response.status_code == 200
    assert "user@example.com" not in response.json()["text"]


def test_anonymize_hash_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "Contact me at user@example.com",
            "language": "en",
            "operators": {"EMAIL_ADDRESS": {"type": "hash", "params": {"hash_type": "sha256"}}},
        },
    )
    assert response.status_code == 200
    assert "user@example.com" not in response.json()["text"]


def test_anonymize_mask_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "My email is user@example.com",
            "language": "en",
            "operators": {
                "EMAIL_ADDRESS": {
                    "type": "mask",
                    "params": {"masking_char": "*", "chars_to_mask": 5, "from_end": False},
                }
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "user@example.com" not in data["text"]
    assert "*" in data["text"]


def test_anonymize_keep_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "My email is user@example.com",
            "language": "en",
            "operators": {"EMAIL_ADDRESS": {"type": "keep"}},
        },
    )
    assert response.status_code == 200
    assert "user@example.com" in response.json()["text"]


def test_anonymize_response_structure():
    response = client.post(
        "/anonymize",
        json={"text": "Call me at 212-555-5555", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "items" in data
    if data["items"]:
        item = data["items"][0]
        for field in ("operator", "entity_type", "start", "end", "text"):
            assert field in item


def test_anonymize_empty_text():
    response = client.post(
        "/anonymize",
        json={"text": "", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == ""
    assert data["items"] == []


def test_anonymize_batch():
    response = client.post(
        "/anonymize/batch",
        json={
            "texts": [
                "My name is Alice",
                "My email is bob@example.com",
            ],
            "language": "en",
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    for result in results:
        assert "text" in result
        assert "items" in result


def test_anonymize_batch_empty_list():
    response = client.post(
        "/anonymize/batch",
        json={"texts": [], "language": "en"},
    )
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_anonymize_default_operator():
    response = client.post(
        "/anonymize",
        json={
            "text": "Hello John, my phone is 212-555-5555 and SSN is 078-05-1120",
            "language": "en",
            "operators": {
                "DEFAULT": {"type": "redact"},
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "text" in data

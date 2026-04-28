from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_analyze_person():
    response = client.post(
        "/analyze",
        json={"text": "My name is John Smith", "language": "en"},
    )
    assert response.status_code == 200
    entity_types = [e["entity_type"] for e in response.json()["entities"]]
    assert "PERSON" in entity_types


def test_analyze_email():
    response = client.post(
        "/analyze",
        json={"text": "Contact me at test@example.com", "language": "en"},
    )
    assert response.status_code == 200
    entity_types = [e["entity_type"] for e in response.json()["entities"]]
    assert "EMAIL_ADDRESS" in entity_types


def test_analyze_filter_entities():
    response = client.post(
        "/analyze",
        json={
            "text": "My name is Alice and my phone is 212-555-5555",
            "language": "en",
            "entities": ["PERSON"],
        },
    )
    assert response.status_code == 200
    entity_types = {e["entity_type"] for e in response.json()["entities"]}
    assert "PERSON" in entity_types
    assert "PHONE_NUMBER" not in entity_types


def test_analyze_empty_text():
    response = client.post(
        "/analyze",
        json={"text": "", "language": "en"},
    )
    assert response.status_code == 200
    assert response.json()["entities"] == []


def test_analyze_result_structure():
    response = client.post(
        "/analyze",
        json={
            "text": "Email me at user@test.com",
            "language": "en",
            "entities": ["EMAIL_ADDRESS"],
        },
    )
    assert response.status_code == 200
    entities = response.json()["entities"]
    assert len(entities) > 0
    entity = entities[0]
    for field in ("entity_type", "start", "end", "score", "text"):
        assert field in entity
    assert entity["text"] == "user@test.com"


def test_list_entities():
    response = client.get("/analyze/entities")
    assert response.status_code == 200
    entities = response.json()
    assert isinstance(entities, list)
    assert len(entities) > 0
    assert "PERSON" in entities
    assert "EMAIL_ADDRESS" in entities

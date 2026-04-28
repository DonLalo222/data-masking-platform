from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import recognizer_registry as registry

client = TestClient(app)

_TEST_RECOGNIZERS = ["test_emp_recognizer", "test_codename_recognizer"]


@pytest.fixture(autouse=True)
def cleanup():
    """Remove test recognizers before and after each test."""
    for name in _TEST_RECOGNIZERS:
        registry.remove_recognizer(name)
    yield
    for name in _TEST_RECOGNIZERS:
        registry.remove_recognizer(name)


def test_list_recognizers_returns_list():
    response = client.get("/recognizers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # At least the built-in recognizers should be present
    assert len(response.json()) > 0


def test_add_pattern_recognizer():
    response = client.post(
        "/recognizers",
        json={
            "name": "test_emp_recognizer",
            "supported_entity": "EMPLOYEE_ID",
            "supported_language": "en",
            "type": "pattern",
            "patterns": [{"name": "emp_id", "regex": r"EMP\d{6}", "score": 0.9}],
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test_emp_recognizer"


def test_add_deny_list_recognizer():
    response = client.post(
        "/recognizers",
        json={
            "name": "test_codename_recognizer",
            "supported_entity": "PROJECT_CODENAME",
            "supported_language": "en",
            "type": "deny_list",
            "deny_list": ["Project Alpha", "Project Beta"],
        },
    )
    assert response.status_code == 201


def test_pattern_recognizer_detects_entity():
    client.post(
        "/recognizers",
        json={
            "name": "test_emp_recognizer",
            "supported_entity": "EMPLOYEE_ID",
            "supported_language": "en",
            "type": "pattern",
            "patterns": [{"name": "emp_id", "regex": r"EMP\d{6}", "score": 0.9}],
        },
    )

    response = client.post(
        "/analyze",
        json={
            "text": "Employee ID: EMP123456 is on leave",
            "language": "en",
            "entities": ["EMPLOYEE_ID"],
        },
    )
    assert response.status_code == 200
    entity_types = [e["entity_type"] for e in response.json()["entities"]]
    assert "EMPLOYEE_ID" in entity_types


def test_deny_list_recognizer_detects_entity():
    client.post(
        "/recognizers",
        json={
            "name": "test_codename_recognizer",
            "supported_entity": "PROJECT_CODENAME",
            "supported_language": "en",
            "type": "deny_list",
            "deny_list": ["Project Alpha", "Project Beta"],
        },
    )

    response = client.post(
        "/analyze",
        json={
            "text": "We are working on Project Alpha this quarter",
            "language": "en",
            "entities": ["PROJECT_CODENAME"],
        },
    )
    assert response.status_code == 200
    entity_types = [e["entity_type"] for e in response.json()["entities"]]
    assert "PROJECT_CODENAME" in entity_types


def test_custom_recognizer_appears_in_list():
    client.post(
        "/recognizers",
        json={
            "name": "test_emp_recognizer",
            "supported_entity": "EMPLOYEE_ID",
            "supported_language": "en",
            "type": "pattern",
            "patterns": [{"name": "emp_id", "regex": r"EMP\d{6}", "score": 0.9}],
        },
    )
    response = client.get("/recognizers")
    assert response.status_code == 200
    names = [r["name"] for r in response.json()]
    assert "test_emp_recognizer" in names


def test_remove_recognizer():
    client.post(
        "/recognizers",
        json={
            "name": "test_emp_recognizer",
            "supported_entity": "EMPLOYEE_ID",
            "supported_language": "en",
            "type": "pattern",
            "patterns": [{"name": "emp_id", "regex": r"EMP\d{6}", "score": 0.9}],
        },
    )
    response = client.delete("/recognizers/test_emp_recognizer")
    assert response.status_code == 204


def test_remove_nonexistent_recognizer():
    response = client.delete("/recognizers/does_not_exist_xyz")
    assert response.status_code == 404


def test_add_pattern_recognizer_without_patterns_returns_400():
    response = client.post(
        "/recognizers",
        json={
            "name": "bad_recognizer",
            "supported_entity": "SOMETHING",
            "supported_language": "en",
            "type": "pattern",
            "patterns": [],
        },
    )
    assert response.status_code == 400


def test_add_deny_list_recognizer_without_list_returns_400():
    response = client.post(
        "/recognizers",
        json={
            "name": "bad_recognizer",
            "supported_entity": "SOMETHING",
            "supported_language": "en",
            "type": "deny_list",
            "deny_list": [],
        },
    )
    assert response.status_code == 400

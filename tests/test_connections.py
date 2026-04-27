from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    store.connections.clear()
    store.rules.clear()
    yield
    store.connections.clear()
    store.rules.clear()


def test_create_connection():
    response = client.post(
        "/connections",
        json={
            "name": "test-sqlite",
            "db_type": "sqlite",
            "database": ":memory:",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-sqlite"
    assert data["db_type"] == "sqlite"
    assert "id" in data


def test_list_connections_empty():
    response = client.get("/connections")
    assert response.status_code == 200
    assert response.json() == []


def test_list_connections():
    client.post(
        "/connections",
        json={"name": "conn1", "db_type": "sqlite", "database": ":memory:"},
    )
    client.post(
        "/connections",
        json={"name": "conn2", "db_type": "sqlite", "database": ":memory:"},
    )
    response = client.get("/connections")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_connection():
    create_resp = client.post(
        "/connections",
        json={"name": "my-conn", "db_type": "sqlite", "database": "test.db"},
    )
    conn_id = create_resp.json()["id"]

    response = client.get(f"/connections/{conn_id}")
    assert response.status_code == 200
    assert response.json()["id"] == conn_id


def test_get_connection_not_found():
    response = client.get("/connections/nonexistent-id")
    assert response.status_code == 404


def test_delete_connection():
    create_resp = client.post(
        "/connections",
        json={"name": "del-conn", "db_type": "sqlite", "database": ":memory:"},
    )
    conn_id = create_resp.json()["id"]

    del_resp = client.delete(f"/connections/{conn_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/connections/{conn_id}")
    assert get_resp.status_code == 404


def test_delete_connection_not_found():
    response = client.delete("/connections/nonexistent-id")
    assert response.status_code == 404


def test_test_connection_sqlite_memory():
    create_resp = client.post(
        "/connections",
        json={"name": "sqlite-mem", "db_type": "sqlite", "database": ":memory:"},
    )
    conn_id = create_resp.json()["id"]

    test_resp = client.post(f"/connections/{conn_id}/test")
    assert test_resp.status_code == 200
    assert test_resp.json()["status"] == "ok"

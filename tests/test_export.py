from __future__ import annotations

import sqlite3
import tempfile
import os
import json

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


@pytest.fixture()
def sqlite_db_with_data():
    """Create a temporary SQLite database with sample data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, age INTEGER)"
    )
    conn.executemany(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        [
            (1, "Alice", "alice@example.com", 34),
            (2, "Bob", "bob@example.com", 25),
            (3, "Charlie", "charlie@example.com", 42),
        ],
    )
    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


@pytest.fixture()
def connection_id(sqlite_db_with_data):
    resp = client.post(
        "/connections",
        json={"name": "test-db", "db_type": "sqlite", "database": sqlite_db_with_data},
    )
    return resp.json()["id"]


@pytest.fixture()
def rule_id(connection_id):
    resp = client.post(
        "/rules",
        json={
            "name": "test-rule",
            "connection_id": connection_id,
            "table": "users",
            "column_rules": [
                {"column": "id", "strategy": "keep", "options": {}},
                {"column": "name", "strategy": "anonymize", "options": {}},
                {"column": "email", "strategy": "obfuscate", "options": {}},
                {"column": "age", "strategy": "generalize", "options": {"bucket_size": 10}},
            ],
        },
    )
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Schema introspection
# ---------------------------------------------------------------------------

def test_list_tables(connection_id):
    resp = client.get(f"/connections/{connection_id}/schema/tables")
    assert resp.status_code == 200
    tables = resp.json()
    assert "users" in tables


def test_list_columns(connection_id):
    resp = client.get(f"/connections/{connection_id}/schema/tables/users/columns")
    assert resp.status_code == 200
    columns = resp.json()
    col_names = [c["name"] for c in columns]
    assert "id" in col_names
    assert "name" in col_names
    assert "email" in col_names
    assert "age" in col_names


# ---------------------------------------------------------------------------
# Rules CRUD
# ---------------------------------------------------------------------------

def test_create_and_get_rule(connection_id):
    resp = client.post(
        "/rules",
        json={
            "name": "my-rule",
            "connection_id": connection_id,
            "table": "users",
            "column_rules": [{"column": "name", "strategy": "anonymize", "options": {}}],
        },
    )
    assert resp.status_code == 201
    rule = resp.json()
    assert rule["name"] == "my-rule"

    get_resp = client.get(f"/rules/{rule['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == rule["id"]


def test_update_rule(connection_id):
    create_resp = client.post(
        "/rules",
        json={
            "name": "old-name",
            "connection_id": connection_id,
            "table": "users",
            "column_rules": [],
        },
    )
    rule_id = create_resp.json()["id"]

    update_resp = client.put(f"/rules/{rule_id}", json={"name": "new-name"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "new-name"


def test_delete_rule(connection_id):
    create_resp = client.post(
        "/rules",
        json={
            "name": "to-delete",
            "connection_id": connection_id,
            "table": "users",
            "column_rules": [],
        },
    )
    rule_id = create_resp.json()["id"]

    del_resp = client.delete(f"/rules/{rule_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/rules/{rule_id}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def test_export_csv(rule_id):
    resp = client.post("/export", json={"rule_id": rule_id, "format": "csv", "limit": 10})
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    assert "id" in content
    assert "name" in content


def test_export_json(rule_id):
    resp = client.post("/export", json={"rule_id": rule_id, "format": "json", "limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3
    for row in data:
        assert row["name"] is None
        assert "@" in row["email"]
        assert "-" in str(row["age"])


def test_export_rule_not_found():
    resp = client.post("/export", json={"rule_id": "nonexistent", "format": "csv", "limit": 10})
    assert resp.status_code == 404


def test_export_limit(rule_id):
    resp = client.post("/export", json={"rule_id": rule_id, "format": "json", "limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

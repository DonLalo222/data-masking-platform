"""Tests for CSV upload and batch processing endpoints."""
from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import audit_log

SAMPLE_CSV = (
    "rut,nombre,diagnostico,notas\n"
    "15.234.567-K,Juan Pérez,Hipertensión,"
    '"El paciente Juan Pérez con RUT 15.234.567-K acude a control"\n'
    "10.987.654-3,María Silva,Diabetes,"
    '"Sra. María (10.987.654-3) presenta glicemia elevada"\n'
)


@pytest.fixture(scope="module")
def client():
    """TestClient that runs the app lifespan so clinical recognizers are registered."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_audit():
    audit_log.clear()


def _csv_file(content: str = SAMPLE_CSV, filename: str = "test.csv"):
    return ("file", (filename, io.BytesIO(content.encode("utf-8")), "text/csv"))


def test_csv_process_minsal(client):
    """POST /csv/process with MINSAL framework returns 2 rows and anonymized RUT."""
    response = client.post(
        "/csv/process",
        files=[_csv_file()],
        data={"config": json.dumps({"framework": "minsal", "language": "es"})},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["framework"] == "minsal"
    assert data["total_rows"] == 2
    # RUT should be anonymized in the 'notas' column
    for row in data["rows"]:
        assert "15.234.567-K" not in row["anonymized"].get("notas", "")


def test_csv_process_hipaa(client):
    """POST /csv/process with HIPAA framework returns a valid overall_risk_level."""
    response = client.post(
        "/csv/process",
        files=[_csv_file()],
        data={"config": json.dumps({"framework": "hipaa", "language": "es"})},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data["overall_risk_level"], str)
    assert data["overall_risk_level"] in ("low", "medium", "high")


def test_csv_process_iso25237(client):
    """POST /csv/process with iso25237 should produce pseudonym tokens ([...]) in notas."""
    response = client.post(
        "/csv/process",
        files=[_csv_file()],
        data={"config": json.dumps({"framework": "iso25237", "language": "es"})},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # At least one anonymized notas cell should contain a [ token
    notas_cells = [r["anonymized"].get("notas", "") for r in data["rows"]]
    assert any("[" in cell for cell in notas_cells), (
        f"Expected pseudonym tokens in notas but got: {notas_cells}"
    )


def test_csv_download(client):
    """POST /csv/process/download should return a text/csv response."""
    response = client.post(
        "/csv/process/download",
        files=[_csv_file()],
        data={"config": json.dumps({"framework": "minsal", "language": "es"})},
    )
    assert response.status_code == 200, response.text
    content_type = response.headers.get("content-type", "")
    assert "text/csv" in content_type


def test_csv_invalid_format(client):
    """Uploading a .txt file should return HTTP 400."""
    response = client.post(
        "/csv/process",
        files=[_csv_file(filename="data.txt")],
        data={"config": json.dumps({"framework": "minsal", "language": "es"})},
    )
    assert response.status_code == 400


def test_csv_invalid_config(client):
    """Uploading a valid CSV with malformed JSON config should return HTTP 422."""
    response = client.post(
        "/csv/process",
        files=[_csv_file()],
        data={"config": "not-valid-json"},
    )
    assert response.status_code == 422


def test_csv_process_response_structure(client):
    """Each row in the response must have required fields."""
    response = client.post(
        "/csv/process",
        files=[_csv_file()],
        data={"config": json.dumps({"framework": "minsal", "language": "es"})},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    for row in data["rows"]:
        assert "row_index" in row
        assert "original" in row
        assert "anonymized" in row
        assert "entities_found" in row
        assert "risk_score" in row
        assert isinstance(row["entities_found"], list)
        assert row["risk_score"] is None or isinstance(row["risk_score"], float)

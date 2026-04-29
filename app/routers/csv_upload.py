"""CSV upload and batch processing router."""
from __future__ import annotations

import io
import json
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.models.csv_processing import CsvProcessRequest, CsvProcessResponse
from app.services import csv_processor

router = APIRouter(prefix="/csv", tags=["CSV Processing"])

# ---------------------------------------------------------------------------
# Framework metadata for the /csv/frameworks endpoint
# ---------------------------------------------------------------------------

_CSV_FRAMEWORKS = [
    {
        "id": "minsal",
        "name": "MINSAL Chile / Ley 19.628",
        "description": "Chilean Ministry of Health anonymization profile.",
        "default_text_handling": "NLP anonymization with Chilean entity recognizers",
    },
    {
        "id": "hipaa",
        "name": "HIPAA Safe Harbor",
        "description": "Removes all 18 PHI categories (45 CFR §164.514(b)(2)).",
        "default_text_handling": "NLP anonymization with HIPAA Safe Harbor operators",
    },
    {
        "id": "iso25237",
        "name": "ISO 25237",
        "description": "Deterministic HMAC-SHA256 pseudonymization (ISO 25237:2017).",
        "default_text_handling": "Pseudonymization — entities replaced with [TYPE_token] tokens",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/frameworks")
def list_csv_frameworks() -> List[dict]:
    """Return available frameworks with their default column handling descriptions."""
    return _CSV_FRAMEWORKS


@router.post("/process", response_model=CsvProcessResponse)
async def process_csv_upload(
    file: UploadFile = File(..., description="CSV file to process"),
    config: str = Form(
        '{"framework":"minsal","language":"es"}',
        description="JSON-encoded CsvProcessRequest",
    ),
) -> CsvProcessResponse:
    """Upload a CSV file and anonymize it with the specified compliance framework.

    - **file**: The CSV file (max 10 MB).
    - **config**: JSON string with processing options (framework, language, etc.).
    """
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    content = await file.read()

    # Guard against files that sneak past the size check (e.g. size not set)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        req = CsvProcessRequest.model_validate_json(config)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid config JSON: {exc}") from exc

    return csv_processor.process_csv(content, req)


@router.post("/process/download")
async def process_csv_download(
    file: UploadFile = File(..., description="CSV file to process"),
    config: str = Form(
        '{"framework":"minsal","language":"es"}',
        description="JSON-encoded CsvProcessRequest",
    ),
) -> StreamingResponse:
    """Upload a CSV file, anonymize it, and return the result as a downloadable CSV.

    - **file**: The CSV file (max 10 MB).
    - **config**: JSON string with processing options.
    """
    if not (file.filename or "").endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    try:
        req = CsvProcessRequest.model_validate_json(config)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid config JSON: {exc}") from exc

    response = csv_processor.process_csv(content, req)
    csv_content = csv_processor.response_to_csv(response)

    original_filename = file.filename or "data.csv"
    download_name = f"anonymized_{original_filename}"

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )

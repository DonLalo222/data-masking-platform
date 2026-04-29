from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CsvColumnMapping(BaseModel):
    """Maps a CSV column name to processing options."""

    column: str = Field(..., description="Column name in the CSV header")
    process_as: str = Field(
        "text",
        description="'text' = run NLP anonymization, 'structured' = apply operator directly, 'skip' = leave unchanged",
    )
    entity_type: Optional[str] = Field(
        None,
        description="For structured columns: entity type to apply operator to (e.g. 'CL_RUT')",
    )
    operator: Optional[str] = Field(
        None,
        description="For structured columns: operator to apply ('replace','redact','hash','mask','pseudonymize')",
    )
    operator_params: Optional[Dict[str, Any]] = Field(None)


class CsvProcessRequest(BaseModel):
    framework: str = Field(
        "minsal",
        description="Compliance framework: 'minsal', 'hipaa', 'iso25237'",
    )
    language: str = Field("es")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0)
    text_columns: Optional[List[str]] = Field(
        None,
        description="Column names containing free text to run NLP on. If None, all string columns are processed.",
    )
    structured_columns: Optional[List[CsvColumnMapping]] = Field(
        None,
        description="Columns with known PII to process with a specific operator",
    )
    delimiter: str = Field(",", description="CSV delimiter")
    encoding: str = Field("utf-8", description="CSV file encoding")


class CsvRowResult(BaseModel):
    row_index: int
    original: Dict[str, Any]
    anonymized: Dict[str, Any]
    entities_found: List[str]
    risk_score: Optional[float]


class CsvProcessResponse(BaseModel):
    framework: str
    total_rows: int
    columns_processed: List[str]
    rows: List[CsvRowResult]
    overall_risk_score: float
    overall_risk_level: str
    audit_id: str
    processing_time_ms: float

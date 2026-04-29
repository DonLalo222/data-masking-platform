"""CSV batch processing service for compliance frameworks."""
from __future__ import annotations

import csv
import io
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from presidio_analyzer import RecognizerResult

from app.models.csv_processing import (
    CsvColumnMapping,
    CsvProcessRequest,
    CsvProcessResponse,
    CsvRowResult,
)
from app.services import analyzer as analyzer_svc
from app.services import anonymizer as anonymizer_svc
from app.services import audit_log, pseudonymization, risk_scoring

# ---------------------------------------------------------------------------
# Framework default operators (mirrors compliance.py)
# ---------------------------------------------------------------------------

_HIPAA_SAFE_HARBOR_OPERATORS: Dict[str, dict] = {
    entity: {"type": "replace", "params": {"new_value": f"<{entity}>"}}
    for entity in [
        "PERSON",
        "LOCATION",
        "ADDRESS",
        "DATE_TIME",
        "AGE",
        "PHONE_NUMBER",
        "EMAIL_ADDRESS",
        "US_SSN",
        "US_DRIVER_LICENSE",
        "US_BANK_NUMBER",
        "IBAN_CODE",
        "CREDIT_CARD",
        "URL",
        "IP_ADDRESS",
        "MEDICAL_LICENSE",
        "US_PASSPORT",
        "NRP",
    ]
}
_HIPAA_SAFE_HARBOR_OPERATORS["DEFAULT"] = {"type": "replace", "params": {}}

_MINSAL_OPERATORS: Dict[str, dict] = {
    "CL_RUT": {"type": "replace", "params": {"new_value": "<RUT>"}},
    "CL_PHONE_NUMBER": {
        "type": "mask",
        "params": {"masking_char": "*", "chars_to_mask": 6, "from_end": True},
    },
    "CL_FONASA_ISAPRE": {"type": "replace", "params": {"new_value": "<PREVISION>"}},
    "CL_FICHA_CLINICA": {"type": "replace", "params": {"new_value": "<FICHA>"}},
    "CL_POSTAL_CODE": {"type": "replace", "params": {"new_value": "<CP>"}},
    "CL_REGION": {"type": "keep"},
    "PERSON": {"type": "replace", "params": {"new_value": "<PACIENTE>"}},
    "EMAIL_ADDRESS": {"type": "redact"},
    "DATE_TIME": {"type": "replace", "params": {"new_value": "<FECHA>"}},
    "LOCATION": {"type": "replace", "params": {"new_value": "<LUGAR>"}},
    "DEFAULT": {"type": "replace"},
}

_FRAMEWORK_OPERATORS: Dict[str, Dict[str, dict]] = {
    "minsal": _MINSAL_OPERATORS,
    "hipaa": _HIPAA_SAFE_HARBOR_OPERATORS,
    "hipaa-safe-harbor": _HIPAA_SAFE_HARBOR_OPERATORS,
    "iso25237": _MINSAL_OPERATORS,  # iso25237 uses pseudonymization, not standard operators
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_operators(framework: str) -> Dict[str, dict]:
    """Return the default operator map for the given framework."""
    return _FRAMEWORK_OPERATORS.get(framework, _MINSAL_OPERATORS)


def _apply_structured_column(
    cell_value: str,
    mapping: CsvColumnMapping,
    framework: str,
) -> str:
    """Apply an operator directly to the whole cell value (no NLP)."""
    if not cell_value:
        return cell_value

    entity_type = mapping.entity_type or "CUSTOM"
    operator_name = mapping.operator or "replace"
    operator_params = mapping.operator_params or {}

    # Build a fake RecognizerResult covering the entire cell
    fake_result = RecognizerResult(
        entity_type=entity_type,
        start=0,
        end=len(cell_value),
        score=1.0,
    )
    operators = {
        entity_type: {"type": operator_name, "params": operator_params},
    }
    result = anonymizer_svc.anonymize_text(
        text=cell_value,
        analyzer_results=[fake_result],
        operators=operators,
    )
    return result.text


def _anonymize_text_column(
    cell_value: str,
    language: str,
    score_threshold: float,
    framework: str,
    operators: Dict[str, dict],
    pseudonym_key: Optional[str] = None,
) -> tuple[str, List[str]]:
    """Run NLP analysis + anonymization on a text cell.

    Returns (anonymized_text, entity_types_found).
    """
    if not cell_value:
        return cell_value, []

    analyzer_results = analyzer_svc.analyze_text(
        text=cell_value,
        language=language,
        score_threshold=score_threshold,
    )
    entities = [r.entity_type for r in analyzer_results]

    if framework == "iso25237":
        key = pseudonym_key or pseudonymization.get_default_key()
        anonymized_text, _ = pseudonymization.pseudonymize_text(
            text=cell_value,
            analyzer_results=analyzer_results,
            key=key,
        )
    else:
        result = anonymizer_svc.anonymize_text(
            text=cell_value,
            analyzer_results=analyzer_results,
            operators=operators,
        )
        anonymized_text = result.text

    return anonymized_text, entities


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_csv(
    file_content: bytes,
    request: CsvProcessRequest,
) -> CsvProcessResponse:
    """Process a CSV file according to the given request configuration.

    Args:
        file_content: Raw bytes of the uploaded CSV file.
        request: Processing configuration (framework, column mappings, etc.).

    Returns:
        A :class:`CsvProcessResponse` with anonymized rows and risk metrics.
    """
    start_time = time.perf_counter()

    text = file_content.decode(request.encoding)
    reader = csv.DictReader(io.StringIO(text), delimiter=request.delimiter)

    operators = _get_operators(request.framework)

    # Build lookup maps for structured columns
    structured_map: Dict[str, CsvColumnMapping] = {}
    if request.structured_columns:
        for mapping in request.structured_columns:
            structured_map[mapping.column] = mapping

    rows: List[CsvRowResult] = []
    all_risk_scores: List[float] = []
    columns_processed: Set[str] = set()

    for row_index, row in enumerate(reader):
        original: Dict[str, Any] = dict(row)
        anonymized: Dict[str, Any] = dict(row)
        row_entities: List[str] = []

        for col, cell_value in row.items():
            cell_str = str(cell_value) if cell_value is not None else ""

            # Structured column: apply operator directly
            if col in structured_map:
                mapping = structured_map[col]
                if mapping.process_as == "skip":
                    pass
                elif mapping.process_as == "structured":
                    anonymized[col] = _apply_structured_column(cell_str, mapping, request.framework)
                    columns_processed.add(col)
                else:
                    # Default: treat as text
                    anon_text, entities = _anonymize_text_column(
                        cell_str, request.language, request.score_threshold,
                        request.framework, operators,
                    )
                    anonymized[col] = anon_text
                    row_entities.extend(entities)
                    columns_processed.add(col)
                continue

            # Skip columns not in text_columns if text_columns is specified
            if request.text_columns is not None and col not in request.text_columns:
                continue

            # Only process string-like (non-empty) cells
            if not cell_str:
                continue

            anon_text, entities = _anonymize_text_column(
                cell_str, request.language, request.score_threshold,
                request.framework, operators,
            )
            anonymized[col] = anon_text
            row_entities.extend(entities)
            columns_processed.add(col)

        risk_result = risk_scoring.score(row_entities)
        row_risk_score = risk_result["risk_score"]
        all_risk_scores.append(row_risk_score)

        rows.append(
            CsvRowResult(
                row_index=row_index,
                original=original,
                anonymized=anonymized,
                entities_found=list(set(row_entities)),
                risk_score=row_risk_score,
            )
        )

    overall_risk_score = sum(all_risk_scores) / len(all_risk_scores) if all_risk_scores else 0.0
    overall_risk_result = risk_scoring.score(
        [e for r in rows for e in r.entities_found]
    )
    overall_risk_level = overall_risk_result["risk_level"]

    audit_id = str(uuid.uuid4())
    processing_time_ms = (time.perf_counter() - start_time) * 1000

    all_entities = [e for r in rows for e in r.entities_found]
    audit_log.record(
        operation="CSV_PROCESS",
        language=request.language,
        framework=request.framework,
        entities_found=all_entities,
        operators_applied=list(columns_processed),
        input_length=len(text),
        risk_score=overall_risk_score,
        metadata={"audit_id": audit_id, "total_rows": len(rows)},
    )

    return CsvProcessResponse(
        framework=request.framework,
        total_rows=len(rows),
        columns_processed=sorted(columns_processed),
        rows=rows,
        overall_risk_score=round(overall_risk_score, 4),
        overall_risk_level=overall_risk_level,
        audit_id=audit_id,
        processing_time_ms=round(processing_time_ms, 2),
    )


def response_to_csv(response: CsvProcessResponse) -> str:
    """Convert the anonymized rows in a :class:`CsvProcessResponse` back to CSV string.

    Args:
        response: The processing response containing anonymized rows.

    Returns:
        A CSV-formatted string of the anonymized data.
    """
    if not response.rows:
        return ""

    output = io.StringIO()
    fieldnames = list(response.rows[0].anonymized.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in response.rows:
        writer.writerow(row.anonymized)
    return output.getvalue()

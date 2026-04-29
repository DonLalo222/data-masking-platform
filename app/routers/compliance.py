"""Compliance framework router — /compliance prefix.

Supports:
- HIPAA Safe Harbor (45 CFR §164.514(b))
- HIPAA Expert Determination (45 CFR §164.514(b)(1))
- MINSAL Chile / Ley 19.628
- ISO 25237 — Pseudonymization with HMAC-SHA256
- ISO 29101 — Audit trail
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Query

from app.models.compliance import (
    AuditLogEntry,
    AuditLogResponse,
    ComplianceAnonymizeRequest,
    ComplianceAnonymizeResponse,
    DepseudonymizeRequest,
    DepseudonymizeResponse,
    FrameworkInfo,
    PseudonymizeRequest,
    PseudonymizeResponse,
    RiskScoreRequest,
    RiskScoreResponse,
)
from app.services import analyzer as analyzer_svc
from app.services import anonymizer as anonymizer_svc
from app.services import audit_log, pseudonymization, risk_scoring

router = APIRouter(prefix="/compliance", tags=["Compliance"])

# ---------------------------------------------------------------------------
# Framework entity lists
# ---------------------------------------------------------------------------

HIPAA_SAFE_HARBOR_ENTITIES: List[str] = [
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

MINSAL_ENTITIES: List[str] = [
    # Identificadores personales chilenos
    "CL_RUT",
    "CL_PASAPORTE",
    "CL_CEDULA_EXTRANJERIA",
    "CL_NSS",
    # Datos clínicos
    "CL_FICHA_CLINICA",
    "CL_FONASA_ISAPRE",
    # Datos de contacto/ubicación
    "CL_PHONE",
    "CL_REGION",
    # Entidades genéricas de Presidio
    "PERSON",
    "EMAIL_ADDRESS",
    "DATE_TIME",
    "LOCATION",
    "ADDRESS",
    "PHONE_NUMBER",
    # Datos financieros que pueden aparecer en fichas digitales
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "URL",
]

# ---------------------------------------------------------------------------
# Default operators per framework
# ---------------------------------------------------------------------------

_HIPAA_SAFE_HARBOR_OPERATORS: Dict[str, dict] = {
    entity: {"type": "replace", "params": {"new_value": f"<{entity}>"}}
    for entity in HIPAA_SAFE_HARBOR_ENTITIES
}
_HIPAA_SAFE_HARBOR_OPERATORS["DEFAULT"] = {"type": "replace", "params": {}}

_MINSAL_OPERATORS: Dict[str, dict] = {
    # Identificadores: reemplazar con placeholder
    "CL_RUT": {"type": "replace", "params": {"new_value": "<RUT>"}},
    "CL_PASAPORTE": {"type": "replace", "params": {"new_value": "<PASAPORTE>"}},
    "CL_CEDULA_EXTRANJERIA": {"type": "replace", "params": {"new_value": "<CEDULA_EXT>"}},
    "CL_NSS": {"type": "replace", "params": {"new_value": "<NSS>"}},
    # Ficha clínica: reemplazar (es un identificador directo)
    "CL_FICHA_CLINICA": {"type": "replace", "params": {"new_value": "<FICHA>"}},
    # Previsión: reemplazar con placeholder genérico
    "CL_FONASA_ISAPRE": {"type": "replace", "params": {"new_value": "<PREVISION>"}},
    # Teléfonos: enmascarar últimos 6 dígitos
    "CL_PHONE": {"type": "mask", "params": {"masking_char": "*", "chars_to_mask": 6, "from_end": True}},
    "PHONE_NUMBER": {"type": "mask", "params": {"masking_char": "*", "chars_to_mask": 6, "from_end": True}},
    # Región: conservar (dato geográfico agregado, no re-identificador)
    "CL_REGION": {"type": "keep"},
    # Persona: reemplazar
    "PERSON": {"type": "replace", "params": {"new_value": "<PACIENTE>"}},
    # Email: eliminar completamente
    "EMAIL_ADDRESS": {"type": "redact"},
    # Fecha: reemplazar con placeholder de año (Presidio no extrae el año
    # directamente; se usa un placeholder genérico conforme a Ley 20.584)
    "DATE_TIME": {"type": "replace", "params": {"new_value": "<AÑO>"}},
    # Dirección: reemplazar
    "LOCATION": {"type": "replace", "params": {"new_value": "<LUGAR>"}},
    "ADDRESS": {"type": "replace", "params": {"new_value": "<DIRECCION>"}},
    # Datos financieros: eliminar completamente
    "CREDIT_CARD": {"type": "redact"},
    "IBAN_CODE": {"type": "redact"},
    # Datos digitales: eliminar
    "IP_ADDRESS": {"type": "redact"},
    "URL": {"type": "redact"},
    # Fallback
    "DEFAULT": {"type": "replace"},
}

# ---------------------------------------------------------------------------
# Framework metadata
# ---------------------------------------------------------------------------

_FRAMEWORKS: List[FrameworkInfo] = [
    FrameworkInfo(
        id="hipaa-safe-harbor",
        name="HIPAA Safe Harbor",
        description=(
            "Removes all 18 categories of PHI identifiers as defined by the "
            "HIPAA Safe Harbor method (45 CFR §164.514(b)(2))."
        ),
        jurisdiction="United States",
        entities_covered=HIPAA_SAFE_HARBOR_ENTITIES,
        references=[
            "45 CFR §164.514(b)",
            "https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html",
        ],
    ),
    FrameworkInfo(
        id="hipaa-expert-determination",
        name="HIPAA Expert Determination",
        description=(
            "Statistical risk assessment for re-identification based on "
            "HIPAA Expert Determination method (45 CFR §164.514(b)(1)). "
            "Inspired by NIST SP 800-188 and k-anonymity."
        ),
        jurisdiction="United States",
        entities_covered=list(risk_scoring._ENTITY_RISK_WEIGHTS.keys()),
        references=[
            "45 CFR §164.514(b)(1)",
            "NIST SP 800-188",
        ],
    ),
    FrameworkInfo(
        id="minsal",
        name="MINSAL Chile / Ley 19.628 / Ley 20.584",
        description=(
            "Anonymization profile for the Chilean Ministry of Health (MINSAL) "
            "aligned with Ley 19.628 de Protección de la Vida Privada and "
            "Ley 20.584 sobre Derechos y Deberes de los Pacientes."
        ),
        jurisdiction="Chile",
        entities_covered=MINSAL_ENTITIES,
        references=[
            "Ley 19.628 (Chile)",
            "Ley 20.584 (Chile)",
            "https://www.bcn.cl/leychile/navegar?idNorma=141599",
            "https://www.bcn.cl/leychile/navegar?idNorma=1039348",
        ],
    ),
    FrameworkInfo(
        id="iso-25237",
        name="ISO 25237",
        description=(
            "Formal pseudonymization with deterministic HMAC-SHA256 tokens "
            "and reversible mapping (ISO 25237:2017 Health informatics — Pseudonymization)."
        ),
        jurisdiction="International",
        entities_covered=list(risk_scoring._ENTITY_RISK_WEIGHTS.keys()),
        references=[
            "ISO 25237:2017",
            "https://www.iso.org/standard/63553.html",
        ],
    ),
    FrameworkInfo(
        id="iso-29101",
        name="ISO 29101",
        description=(
            "Audit trail of all PII processing operations "
            "(ISO 29101:2018 Information technology — Privacy architecture framework)."
        ),
        jurisdiction="International",
        entities_covered=[],
        references=[
            "ISO 29101:2018",
            "https://www.iso.org/standard/45124.html",
        ],
    ),
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _merge_operators(base: Dict[str, dict], overrides: Optional[Dict] = None) -> Dict[str, dict]:
    """Merge base framework operators with optional per-request overrides."""
    if not overrides:
        return base
    merged = dict(base)
    for entity, cfg in overrides.items():
        merged[entity] = cfg.model_dump(exclude_none=True)
    return merged


def _run_compliance_anonymize(
    request: ComplianceAnonymizeRequest,
    framework: str,
    entities: List[str],
    default_operators: Dict[str, dict],
) -> ComplianceAnonymizeResponse:
    """Shared logic for compliance anonymization endpoints."""
    # 1. Analyze text
    analyzer_results = analyzer_svc.analyze_text(
        text=request.text,
        language=request.language,
        score_threshold=request.score_threshold,
    )

    # 2. Merge operators
    operators = _merge_operators(default_operators, request.additional_operators)

    # 3. Anonymize
    result = anonymizer_svc.anonymize_text(
        text=request.text,
        analyzer_results=analyzer_results,
        operators=operators,
    )

    # 4. Risk scoring
    entities_found = [r.entity_type for r in analyzer_results]
    risk_result = risk_scoring.score(entities_found)

    # 5. Generate audit ID
    audit_id = str(uuid.uuid4())

    # 6. Record audit entry
    operators_applied = list({r.entity_type for r in analyzer_results})
    audit_log.record(
        operation="anonymize",
        language=request.language,
        framework=framework,
        entities_found=entities_found,
        operators_applied=operators_applied,
        input_length=len(request.text),
        risk_score=risk_result["risk_score"],
        metadata={"audit_id": audit_id},
    )

    # 7. Build response items
    items = [
        {
            "operator": item.operator,
            "entity_type": item.entity_type,
            "start": item.start,
            "end": item.end,
            "text": item.text,
        }
        for item in result.items
    ]

    return ComplianceAnonymizeResponse(
        text=result.text,
        items=items,
        framework=framework,
        entities_covered=entities,
        risk_score=risk_result["risk_score"],
        risk_level=risk_result["risk_level"],
        audit_id=audit_id,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/frameworks", response_model=List[FrameworkInfo])
def list_frameworks() -> List[FrameworkInfo]:
    """List all available compliance frameworks with metadata."""
    return _FRAMEWORKS


@router.post("/hipaa/safe-harbor", response_model=ComplianceAnonymizeResponse)
def hipaa_safe_harbor(request: ComplianceAnonymizeRequest) -> ComplianceAnonymizeResponse:
    """Anonymize text using the HIPAA Safe Harbor profile (45 CFR §164.514(b)(2)).

    Removes all 18 categories of PHI identifiers.
    """
    return _run_compliance_anonymize(
        request=request,
        framework="hipaa-safe-harbor",
        entities=HIPAA_SAFE_HARBOR_ENTITIES,
        default_operators=_HIPAA_SAFE_HARBOR_OPERATORS,
    )


@router.post("/hipaa/expert-determination", response_model=RiskScoreResponse)
def hipaa_expert_determination(request: RiskScoreRequest) -> RiskScoreResponse:
    """Calculate re-identification risk score (HIPAA Expert Determination).

    Does not anonymize — returns a statistical risk assessment based on
    NIST SP 800-188 and k-anonymity principles.
    """
    analyzer_results = analyzer_svc.analyze_text(
        text=request.text,
        language=request.language,
        score_threshold=request.score_threshold,
    )

    entities_found = [r.entity_type for r in analyzer_results]
    result = risk_scoring.score(entities_found)

    # Record to audit log
    audit_log.record(
        operation="risk-assessment",
        language=request.language,
        framework="hipaa-expert-determination",
        entities_found=entities_found,
        operators_applied=[],
        input_length=len(request.text),
        risk_score=result["risk_score"],
    )

    return RiskScoreResponse(
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        entities_found=entities_found,
        entity_weights=result["entity_weights"],
        recommendation=result["recommendation"],
        entities_count=result["entities_count"],
    )


@router.post("/minsal", response_model=ComplianceAnonymizeResponse)
def minsal(request: ComplianceAnonymizeRequest) -> ComplianceAnonymizeResponse:
    """Anonymize text using the MINSAL Chile / Ley 19.628 profile."""
    return _run_compliance_anonymize(
        request=request,
        framework="minsal",
        entities=MINSAL_ENTITIES,
        default_operators=_MINSAL_OPERATORS,
    )


@router.post("/iso25237/pseudonymize", response_model=PseudonymizeResponse)
def iso25237_pseudonymize(request: PseudonymizeRequest) -> PseudonymizeResponse:
    """Pseudonymize text using HMAC-SHA256 tokens (ISO 25237:2017)."""
    analyzer_results = analyzer_svc.analyze_text(
        text=request.text,
        language=request.language,
        entities=request.entities,
        score_threshold=request.score_threshold,
    )

    key = request.pseudonym_key or pseudonymization.get_default_key()
    pseudonymized_text, pseudonym_map = pseudonymization.pseudonymize_text(
        text=request.text,
        analyzer_results=analyzer_results,
        key=key,
    )

    entities_found = [r.entity_type for r in analyzer_results]
    audit_log.record(
        operation="pseudonymize",
        language=request.language,
        framework="iso-25237",
        entities_found=entities_found,
        operators_applied=["pseudonymize"],
        input_length=len(request.text),
    )

    return PseudonymizeResponse(
        text=pseudonymized_text,
        pseudonym_map=pseudonym_map,
        entities_count=len(analyzer_results),
    )


@router.post("/iso25237/depseudonymize", response_model=DepseudonymizeResponse)
def iso25237_depseudonymize(request: DepseudonymizeRequest) -> DepseudonymizeResponse:
    """Reverse pseudonymization using the provided token-to-value map (ISO 25237:2017)."""
    restored = pseudonymization.depseudonymize_text(
        pseudonymized_text=request.pseudonymized_text,
        pseudonym_map=request.pseudonym_map,
    )
    return DepseudonymizeResponse(text=restored)


@router.get("/audit-log", response_model=AuditLogResponse)
def get_audit_log(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of entries to return."),
    framework: Optional[str] = Query(None, description="Filter by compliance framework ID."),
) -> AuditLogResponse:
    """Retrieve the audit trail of all compliance operations (ISO 29101)."""
    entries = audit_log.get_entries(limit=limit, framework=framework)
    return AuditLogResponse(
        entries=[AuditLogEntry(**e) for e in entries],
        total=len(entries),
    )

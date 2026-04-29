"""Pydantic models for compliance framework endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.anonymize import AnonymizedItem, OperatorConfig


class ComplianceAnonymizeRequest(BaseModel):
    text: str = Field(..., description="Text whose PII should be anonymized.")
    language: str = Field("es", description="BCP-47 language code.")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0)
    additional_operators: Optional[Dict[str, OperatorConfig]] = Field(
        None,
        description="Override default framework operators for specific entity types.",
    )


class ComplianceAnonymizeResponse(BaseModel):
    text: str = Field(..., description="Anonymized output text.")
    items: List[AnonymizedItem] = Field(..., description="Details of each anonymization applied.")
    framework: str = Field(..., description="Compliance framework used.")
    entities_covered: List[str] = Field(..., description="Entity types covered by this framework.")
    risk_score: Optional[float] = Field(None, description="Re-identification risk score [0, 1].")
    risk_level: Optional[str] = Field(None, description="Risk level: low, medium, or high.")
    audit_id: Optional[str] = Field(None, description="Unique identifier for the audit log entry.")


class RiskScoreRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for re-identification risk.")
    language: str = Field("en", description="BCP-47 language code.")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0)


class RiskScoreResponse(BaseModel):
    risk_score: float = Field(..., description="Re-identification risk score in [0, 1].")
    risk_level: str = Field(..., description="Risk level: low, medium, or high.")
    entities_found: List[str] = Field(..., description="Entity types detected in the text.")
    entity_weights: Dict[str, float] = Field(..., description="Per-entity risk weight mapping.")
    recommendation: str = Field(..., description="Recommendation based on risk level.")
    entities_count: int = Field(..., description="Number of entities detected.")


class PseudonymizeRequest(BaseModel):
    text: str = Field(..., description="Text to pseudonymize.")
    language: str = Field("en", description="BCP-47 language code.")
    entities: Optional[List[str]] = Field(
        None,
        description="Limit pseudonymization to these entity types. Omit to process all.",
    )
    score_threshold: float = Field(0.5, ge=0.0, le=1.0)
    pseudonym_key: Optional[str] = Field(
        None,
        description="Override default pseudonymization key (ISO 25237).",
    )


class PseudonymizeResponse(BaseModel):
    text: str = Field(..., description="Pseudonymized output text.")
    pseudonym_map: Dict[str, str] = Field(
        ...,
        description="Mapping of pseudonym tokens to original values.",
    )
    entities_count: int = Field(..., description="Number of entities pseudonymized.")


class DepseudonymizeRequest(BaseModel):
    pseudonymized_text: str = Field(..., description="Text containing pseudonym tokens.")
    pseudonym_map: Dict[str, str] = Field(
        ...,
        description="Mapping of pseudonym tokens to original values.",
    )


class DepseudonymizeResponse(BaseModel):
    text: str = Field(..., description="Text with pseudonym tokens replaced by original values.")


class AuditLogEntry(BaseModel):
    timestamp: str
    operation: str
    language: str
    framework: str
    entities_found: List[str]
    operators_applied: List[str]
    input_length: int
    risk_score: Optional[float]
    metadata: Dict[str, Any]


class AuditLogResponse(BaseModel):
    entries: List[AuditLogEntry]
    total: int


class FrameworkInfo(BaseModel):
    id: str = Field(..., description="Framework identifier.")
    name: str = Field(..., description="Human-readable framework name.")
    description: str = Field(..., description="Brief description of the framework.")
    jurisdiction: str = Field(..., description="Applicable jurisdiction.")
    entities_covered: List[str] = Field(..., description="Entity types covered.")
    references: List[str] = Field(..., description="Normative references.")

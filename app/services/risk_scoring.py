"""Risk scoring module for HIPAA Expert Determination (45 CFR §164.514(b)(1)).

Inspired by NIST SP 800-188 and k-anonymity principles.
"""

from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# Entity risk weights (0.0 – 1.0)
# ---------------------------------------------------------------------------
_ENTITY_RISK_WEIGHTS: Dict[str, float] = {
    # Direct identifiers
    "PERSON": 1.0,
    "US_SSN": 1.0,
    "CL_RUT": 1.0,
    "ES_DNI": 1.0,
    "ES_NIE": 1.0,
    "EMAIL_ADDRESS": 0.95,
    "PHONE_NUMBER": 0.90,
    "CL_PHONE_NUMBER": 0.90,
    "ES_PHONE_NUMBER": 0.90,
    "MEDICAL_LICENSE": 0.90,
    "CL_FICHA_CLINICA": 0.90,
    "ES_NUHSA": 0.90,
    "CL_FONASA_ISAPRE": 0.85,
    "ES_TARJETA_SANITARIA": 0.85,
    "CREDIT_CARD": 0.85,
    "IBAN_CODE": 0.80,
    "US_BANK_NUMBER": 0.80,
    "US_DRIVER_LICENSE": 0.75,
    "US_PASSPORT": 0.80,
    # Quasi-identifiers
    "DATE_TIME": 0.60,
    "AGE": 0.55,
    "NRP": 0.55,
    "IP_ADDRESS": 0.55,
    "URL": 0.50,
    "LOCATION": 0.50,
    "ADDRESS": 0.50,
    "ES_POSTAL_CODE": 0.45,
    "CL_POSTAL_CODE": 0.45,
    "CL_REGION": 0.40,
    "ES_CIE10_CODE": 0.55,
    "CRYPTO": 0.35,
}

_MAX_CUMULATIVE_WEIGHT: float = 5.0


def score(entities: List[str]) -> Dict:
    """Calculate re-identification risk score for a list of detected entity types.

    Returns a dict with:
    - ``risk_score``: float in [0, 1]
    - ``risk_level``: ``"low"`` | ``"medium"`` | ``"high"``
    - ``entity_weights``: per-entity weight mapping
    - ``recommendation``: descriptive text
    - ``entities_count``: number of entities provided
    """
    entity_weights: Dict[str, float] = {}
    cumulative = 0.0

    for entity in entities:
        weight = _ENTITY_RISK_WEIGHTS.get(entity, 0.30)
        entity_weights[entity] = weight
        cumulative += weight

    risk_score = min(cumulative / _MAX_CUMULATIVE_WEIGHT, 1.0)

    if risk_score < 0.25:
        risk_level = "low"
        recommendation = (
            "Risk of re-identification is low. Standard de-identification measures "
            "are sufficient. Continue monitoring for context changes."
        )
    elif risk_score < 0.60:
        risk_level = "medium"
        recommendation = (
            "Moderate re-identification risk detected. Apply additional anonymization "
            "techniques (e.g., generalization, suppression) and review quasi-identifiers "
            "before sharing data."
        )
    else:
        risk_level = "high"
        recommendation = (
            "High re-identification risk. Expert statistical analysis required per "
            "HIPAA Expert Determination (45 CFR §164.514(b)(1)). Consider k-anonymity "
            "or differential privacy techniques before any disclosure."
        )

    return {
        "risk_score": round(risk_score, 4),
        "risk_level": risk_level,
        "entity_weights": entity_weights,
        "recommendation": recommendation,
        "entities_count": len(entities),
    }

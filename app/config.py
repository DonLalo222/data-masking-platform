from __future__ import annotations

import os

# Spacy NLP model used by Presidio analyzer
NLP_ENGINE_MODEL: str = os.getenv("NLP_ENGINE_MODEL", "en_core_web_lg")

# Default language for analysis/anonymization
DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")

# Default minimum confidence score for entity detection
DEFAULT_SCORE_THRESHOLD: float = float(os.getenv("DEFAULT_SCORE_THRESHOLD", "0.5"))

# Enable/disable Spanish clinical recognizers (ISO/CIE-10/HL7)
ENABLE_CLINICAL_ES: bool = os.getenv("ENABLE_CLINICAL_ES", "true").lower() == "true"

# Enable/disable Chilean clinical recognizers (MINSAL / Ley 19.628)
ENABLE_CLINICAL_CL: bool = os.getenv("ENABLE_CLINICAL_CL", "true").lower() == "true"

# Enable accent-insensitive matching for Chilean geographic entity recognizers.
# When True (default), CL_REGION and CL_COMUNA recognizers detect both
# accented and non-accented text variants (e.g. "Biobio" matches "Biobío").
ENABLE_ACCENT_INSENSITIVE_MATCH: bool = (
    os.getenv("ENABLE_ACCENT_INSENSITIVE_MATCH", "true").lower() == "true"
)

# HMAC key used for deterministic pseudonymization (ISO 25237)
PSEUDONYMIZATION_KEY: str = os.getenv("PSEUDONYMIZATION_KEY", "change-me-in-production-32bytes!")

# Enable/disable ISO 29101 audit log
ENABLE_AUDIT_LOG: bool = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

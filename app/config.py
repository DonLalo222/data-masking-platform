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

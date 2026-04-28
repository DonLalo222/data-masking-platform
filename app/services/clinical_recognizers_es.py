"""Spanish clinical recognizers aligned with ISO, CIE-10 and HL7 standards."""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer
from presidio_analyzer.pattern import Pattern

from app.services.analyzer import get_engine


# ---------------------------------------------------------------------------
# Shared clinical context keywords (boost score when these appear near match)
# ---------------------------------------------------------------------------
_CLINICAL_CONTEXT = [
    "paciente",
    "dni",
    "nie",
    "documento",
    "historia clínica",
    "diagnóstico",
    "tarjeta sanitaria",
    "código postal",
    "teléfono",
    "cip",
    "nuhsa",
    "número de identificación",
    "consulta",
    "médico",
    "hospital",
    "clínica",
]


def _build_recognizers() -> list[PatternRecognizer]:
    """Return fresh PatternRecognizer instances for all Spanish clinical entities."""
    return [
        # DNI — ISO/IEC 7812: 8 digits + check letter
        PatternRecognizer(
            supported_entity="ES_DNI",
            name="EsDniRecognizer",
            supported_language="es",
            patterns=[Pattern(name="ES_DNI", regex=r"\b\d{8}[A-HJ-NP-TV-Z]\b", score=0.85)],
            context=_CLINICAL_CONTEXT,
        ),
        # NIE — foreigner ID: X/Y/Z + 7 digits + check letter
        PatternRecognizer(
            supported_entity="ES_NIE",
            name="EsNieRecognizer",
            supported_language="es",
            patterns=[Pattern(name="ES_NIE", regex=r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b", score=0.85)],
            context=_CLINICAL_CONTEXT,
        ),
        # CIP/SNS health card number — ISO 27799: 4 uppercase letters + 8 digits
        PatternRecognizer(
            supported_entity="ES_TARJETA_SANITARIA",
            name="EsTarjetaSanitariaRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="ES_TARJETA_SANITARIA",
                    regex=r"\b[A-Z]{4}\d{8}\b",
                    score=0.80,
                )
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # NUHSA clinical record number — HL7 / ISO 27799: AN + 10 digits
        PatternRecognizer(
            supported_entity="ES_NUHSA",
            name="EsNuhsaRecognizer",
            supported_language="es",
            patterns=[Pattern(name="ES_NUHSA", regex=r"\bAN\d{10}\b", score=0.85)],
            context=_CLINICAL_CONTEXT,
        ),
        # ICD-10 / CIE-10 diagnostic codes
        PatternRecognizer(
            supported_entity="ES_CIE10_CODE",
            name="EsCie10Recognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="ES_CIE10_CODE",
                    regex=r"\b[A-Z]\d{2}(?:\.\d{1,2})?\b",
                    score=0.70,
                )
            ],
            context=[
                "diagnóstico",
                "código",
                "cie",
                "cie-10",
                "icd",
                "clasificación",
                "enfermedad",
                "patología",
            ],
        ),
        # Spanish phone numbers — E.164 / ITU-T
        PatternRecognizer(
            supported_entity="ES_PHONE_NUMBER",
            name="EsPhoneRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="ES_PHONE_NUMBER",
                    regex=r"(?<!\w)(?:\+34|0034)?[6789]\d{8}\b",
                    score=0.75,
                )
            ],
            context=[
                "teléfono",
                "tel",
                "móvil",
                "contacto",
                "llamar",
                "número",
                "fijo",
                "celular",
            ],
        ),
        # Spanish postal codes — ISO 3166
        PatternRecognizer(
            supported_entity="ES_POSTAL_CODE",
            name="EsPostalCodeRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="ES_POSTAL_CODE",
                    regex=r"\b(?:0[1-9]|[1-4]\d|5[0-2])\d{3}\b",
                    score=0.70,
                )
            ],
            context=[
                "código postal",
                "cp",
                "dirección",
                "localidad",
                "municipio",
                "provincia",
                "domicilio",
            ],
        ),
    ]


def register_clinical_recognizers_es() -> None:
    """Register all Spanish clinical recognizers with the shared AnalyzerEngine.

    This function is idempotent: calling it multiple times will not register
    duplicate recognizers — any existing entry with the same name is replaced.
    """
    engine = get_engine()
    registry = engine.registry

    for recognizer in _build_recognizers():
        # Remove a previous instance of the same recognizer if present so that
        # repeated startup calls (e.g. during tests) do not accumulate duplicates.
        try:
            registry.remove_recognizer(recognizer.name)
        except Exception:
            pass
        registry.add_recognizer(recognizer)


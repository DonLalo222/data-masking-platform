"""Chilean clinical recognizers aligned with MINSAL and Ley 19.628."""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer
from presidio_analyzer.pattern import Pattern

from app.services.analyzer import get_engine


# ---------------------------------------------------------------------------
# Shared clinical context keywords (boost score when these appear near match)
# ---------------------------------------------------------------------------
_CLINICAL_CONTEXT = [
    "paciente",
    "rut",
    "run",
    "documento",
    "ficha clínica",
    "diagnóstico",
    "fonasa",
    "isapre",
    "prevision",
    "previsión",
    "beneficiario",
    "consulta",
    "médico",
    "hospital",
    "clínica",
    "urgencia",
    "atención primaria",
    "cesfam",
    "registro civil",
]


def _build_recognizers() -> list[PatternRecognizer]:
    """Return fresh PatternRecognizer instances for all Chilean clinical entities."""
    return [
        # RUT chileno — with and without dots
        PatternRecognizer(
            supported_entity="CL_RUT",
            name="ClRutRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_RUT_with_dots",
                    regex=r"\b\d{1,2}(?:\.\d{3}){2}-[\dkK]\b",
                    score=0.90,
                ),
                Pattern(
                    name="CL_RUT_no_dots",
                    regex=r"\b\d{7,8}-[\dkK]\b",
                    score=0.85,
                ),
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # Chilean phone numbers — E.164 / ITU-T
        PatternRecognizer(
            supported_entity="CL_PHONE_NUMBER",
            name="ClPhoneRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_PHONE_INTL",
                    regex=r"(?:\+56|0056|56)\s?[2-9]\s?\d{4}\s?\d{4}",
                    score=0.85,
                ),
                Pattern(
                    name="CL_PHONE_LOCAL",
                    regex=r"\b[2-9]\d{7,8}\b",
                    score=0.65,
                ),
            ],
            context=[
                "teléfono",
                "tel",
                "móvil",
                "celular",
                "fono",
                "contacto",
            ],
        ),
        # FONASA / ISAPRE beneficiary number
        PatternRecognizer(
            supported_entity="CL_FONASA_ISAPRE",
            name="ClFonasaIsapreRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_FONASA",
                    regex=r"\bFONASA[-\s]?\d{8,10}\b",
                    score=0.90,
                ),
                Pattern(
                    name="CL_ISAPRE",
                    regex=r"\bISAPRE[-\s]?\d{6,10}\b",
                    score=0.90,
                ),
            ],
            context=[
                "fonasa",
                "isapre",
                "previsión",
                "beneficiario",
                "plan de salud",
            ],
        ),
        # Clinical record / historia clínica number
        PatternRecognizer(
            supported_entity="CL_FICHA_CLINICA",
            name="ClFichaClinicaRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_FICHA_CLINICA",
                    regex=r"\b(?:HC|FC|HCL)[-\s]?\d{4,12}\b",
                    score=0.88,
                ),
            ],
            context=[
                "ficha",
                "historia clínica",
                "registro",
                "número de ficha",
                "código paciente",
            ],
        ),
        # Chilean postal code — 7 digits
        PatternRecognizer(
            supported_entity="CL_POSTAL_CODE",
            name="ClPostalCodeRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_POSTAL_CODE",
                    regex=r"\b\d{7}\b",
                    score=0.60,
                ),
            ],
            context=[
                "código postal",
                "cp",
                "dirección",
                "domicilio",
                "región",
                "comuna",
            ],
        ),
        # Chilean regions — deny_list
        PatternRecognizer(
            supported_entity="CL_REGION",
            name="ClRegionRecognizer",
            supported_language="es",
            deny_list=[
                "Arica y Parinacota",
                "Tarapacá",
                "Antofagasta",
                "Atacama",
                "Coquimbo",
                "Valparaíso",
                "Metropolitana",
                "O'Higgins",
                "Maule",
                "Ñuble",
                "Biobío",
                "La Araucanía",
                "Los Ríos",
                "Los Lagos",
                "Aysén",
                "Magallanes",
            ],
            context=[
                "región",
                "provincia",
                "comuna",
                "localidad",
                "domicilio",
            ],
        ),
    ]


def register_clinical_recognizers_cl() -> None:
    """Register all Chilean clinical recognizers with the shared AnalyzerEngine.

    This function is idempotent: calling it multiple times will not register
    duplicate recognizers — any existing entry with the same name is replaced.
    """
    engine = get_engine()
    registry = engine.registry

    for recognizer in _build_recognizers():
        # Remove any previous instance with the same name before adding the new
        # one, so that repeated calls (e.g. during tests) do not accumulate
        # duplicate entries.
        registry.remove_recognizer(recognizer.name)
        registry.add_recognizer(recognizer)

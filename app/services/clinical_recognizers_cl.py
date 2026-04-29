"""Chilean clinical recognizers aligned with MINSAL, Ley 19.628 and Ley 20.584."""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer
from presidio_analyzer.pattern import Pattern

from app.services.analyzer import get_engine


# ---------------------------------------------------------------------------
# Shared clinical context keywords (boost score when these appear near match)
# ---------------------------------------------------------------------------
_CLINICAL_CONTEXT = [
    "rut",
    "run",
    "paciente",
    "ficha",
    "cédula",
    "cedula",
    "pasaporte",
    "afiliado",
    "fonasa",
    "isapre",
    "previsión",
    "prevision",
    "teléfono",
    "telefono",
    "celular",
    "número",
    "numero",
    "registro",
    "hospital",
    "clínica",
    "clinica",
    "cesfam",
]


def _build_recognizers() -> list[PatternRecognizer]:
    """Return fresh PatternRecognizer instances for all Chilean clinical entities."""
    return [
        # RUT chileno — with dots (score 0.88) and without dots (score 0.82)
        PatternRecognizer(
            supported_entity="CL_RUT",
            name="ClRutRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_RUT_with_dots",
                    regex=r"\b\d{1,3}(?:\.\d{3}){2}-[\dKk]\b",
                    score=0.88,
                ),
                Pattern(
                    name="CL_RUT_no_dots",
                    regex=r"\b\d{7,8}-[\dKk]\b",
                    score=0.82,
                ),
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # Chilean passport — 1-2 uppercase letters + 6-7 digits
        PatternRecognizer(
            supported_entity="CL_PASAPORTE",
            name="ClPasaporteRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_PASAPORTE",
                    regex=r"\b[A-Z]{1,2}\d{6,7}\b",
                    score=0.75,
                ),
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # Cédula de extranjería — PE + 7 digits
        PatternRecognizer(
            supported_entity="CL_CEDULA_EXTRANJERIA",
            name="ClCedulaExtranjeriaRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_CEDULA_EXTRANJERIA",
                    regex=r"\bPE\d{7}\b",
                    score=0.80,
                ),
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # Número de afiliado previsional (FONASA/ISAPRE) — NSS
        PatternRecognizer(
            supported_entity="CL_NSS",
            name="ClNssRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_NSS",
                    regex=r"\b\d{10}\b",
                    score=0.65,
                ),
            ],
            context=[
                "fonasa",
                "isapre",
                "afiliado",
                "cotizante",
                "previsión",
                "prevision",
            ],
        ),
        # Clinical record / ficha clínica number — case insensitive ((?i) flag)
        # Matches: "ficha", "Ficha", "FICHA", "HC", "FC", "HCL" followed by optional
        # separator and 4–10 digits. Example: "Ficha clínica FC-12345", "HC-000456"
        PatternRecognizer(
            supported_entity="CL_FICHA_CLINICA",
            name="ClFichaClinicaRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_FICHA_CLINICA",
                    regex=r"(?i)\b(?:ficha|HC|FC|HCL)\s*[-:]?\s*\d{4,10}\b",
                    score=0.85,
                ),
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # FONASA / ISAPRE health insurer names — deny_list
        PatternRecognizer(
            supported_entity="CL_FONASA_ISAPRE",
            name="ClFonasaIsapreRecognizer",
            supported_language="es",
            deny_list=[
                "FONASA",
                "Banmédica",
                "Colmena",
                "Cruz Blanca",
                "Consalud",
                "Vida Tres",
                "MasVida",
                "Esencial",
            ],
            context=_CLINICAL_CONTEXT,
        ),
        # Chilean regions — deny_list (all 16 regions)
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
        # Chilean phone numbers — E.164 / ITU-T
        # Matches numbers with optional +56/0056/56 country code followed by a
        # local number (9 digits starting with 2-9). Relies on clinical context
        # keywords to avoid false positives on ambiguous digit sequences.
        PatternRecognizer(
            supported_entity="CL_PHONE",
            name="ClPhoneRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_PHONE",
                    regex=r"(?:\+56|0056|56)?[\s\-]?[2-9](?:[\s\-]?\d){8}",
                    score=0.70,
                ),
            ],
            context=_CLINICAL_CONTEXT,
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

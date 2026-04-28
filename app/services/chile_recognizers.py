"""Chilean identification document recognizers."""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer
from presidio_analyzer.pattern import Pattern

from app.services.analyzer import get_engine


# ---------------------------------------------------------------------------
# Shared Chilean context keywords (boost score when these appear near match)
# ---------------------------------------------------------------------------
_CHILE_CONTEXT = [
    "rut",
    "run",
    "cédula",
    "cedula",
    "pasaporte",
    "identificación",
    "identificacion",
    "licencia",
    "teléfono",
    "telefono",
    "celular",
    "fono",
    "número",
    "numero",
]


def _build_recognizers() -> list[PatternRecognizer]:
    """Return fresh PatternRecognizer instances for all Chilean identification entities."""
    return [
        # RUN/RUT chileno — formato con puntos (más específico, score mayor)
        PatternRecognizer(
            supported_entity="CL_RUN",
            name="ClRunWithDotsRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_RUN_dots",
                    regex=r"\b\d{1,3}(?:\.\d{3}){2}-[\dKk]\b",
                    score=0.88,
                ),
                Pattern(
                    name="CL_RUN_plain",
                    regex=r"\b\d{7,8}-[\dKk]\b",
                    score=0.82,
                ),
            ],
            context=_CHILE_CONTEXT,
        ),
        # Pasaporte chileno — 1-2 letras + 6-7 dígitos
        PatternRecognizer(
            supported_entity="CL_PASAPORTE",
            name="ClPasaporteRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_PASAPORTE",
                    regex=r"\b[A-Z]{1,2}\d{6,7}\b",
                    score=0.75,
                )
            ],
            context=_CHILE_CONTEXT,
        ),
        # Cédula de identidad para extranjeros — PE + 7 dígitos
        PatternRecognizer(
            supported_entity="CL_CEDULA_EXTRANJERIA",
            name="ClCedulaExtranjeriaRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_CEDULA_EXTRANJERIA",
                    regex=r"\bPE\d{7}\b",
                    score=0.80,
                )
            ],
            context=_CHILE_CONTEXT,
        ),
        # Licencia de conducir chilena — letra + 7 dígitos
        PatternRecognizer(
            supported_entity="CL_LICENCIA_CONDUCIR",
            name="ClLicenciaConducirRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_LICENCIA_CONDUCIR",
                    regex=r"\b[A-Z]\d{7}\b",
                    score=0.70,
                )
            ],
            context=_CHILE_CONTEXT,
        ),
        # Teléfonos chilenos — +56 / 0056 / 56 + operador + 8 dígitos
        PatternRecognizer(
            supported_entity="CL_PHONE",
            name="ClPhoneRecognizer",
            supported_language="es",
            patterns=[
                Pattern(
                    name="CL_PHONE",
                    regex=r"(?<!\d)(?:\+56|0056|56)?[\s\-]?[2-9](?:[\s\-]?\d){8}(?!\d)",
                    score=0.70,
                )
            ],
            context=[
                "teléfono",
                "telefono",
                "tel",
                "celular",
                "fono",
                "móvil",
                "movil",
                "contacto",
                "llamar",
                "número",
                "numero",
            ],
        ),
    ]


def register_chile_recognizers() -> None:
    """Register all Chilean identification recognizers with the shared AnalyzerEngine.

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

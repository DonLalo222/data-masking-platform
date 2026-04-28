from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import AnalyzerEngine, RecognizerResult

_engine: AnalyzerEngine | None = None


def get_engine() -> AnalyzerEngine:
    """Return the shared AnalyzerEngine instance (lazily initialized)."""
    global _engine
    if _engine is None:
        _engine = AnalyzerEngine()
    return _engine


def analyze_text(
    text: str,
    language: str = "en",
    entities: Optional[List[str]] = None,
    score_threshold: float = 0.5,
) -> List[RecognizerResult]:
    """Analyze *text* and return a list of detected PII entities."""
    engine = get_engine()
    return engine.analyze(
        text=text,
        language=language,
        entities=entities or None,
        score_threshold=score_threshold,
    )


def get_supported_entities(language: str = "en") -> List[str]:
    """Return the list of entity types supported for a given language."""
    engine = get_engine()
    return engine.get_supported_entities(language=language)

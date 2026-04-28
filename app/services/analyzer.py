from __future__ import annotations

from typing import List, Optional

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

_engine: AnalyzerEngine | None = None


def get_engine() -> AnalyzerEngine:
    """Return the shared AnalyzerEngine instance (lazily initialized)."""
    global _engine
    if _engine is None:
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "en", "model_name": "en_core_web_lg"},
                {"lang_code": "es", "model_name": "es_core_news_lg"},
            ],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        _engine = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en", "es"],
        )
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

from __future__ import annotations

from typing import Any, Dict, List, Optional

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import EngineResult, OperatorConfig, RecognizerResult

_engine: AnonymizerEngine | None = None


def get_engine() -> AnonymizerEngine:
    """Return the shared AnonymizerEngine instance (lazily initialized)."""
    global _engine
    if _engine is None:
        _engine = AnonymizerEngine()
    return _engine


def _build_operator_configs(
    operators: Optional[Dict[str, Dict[str, Any]]],
) -> Optional[Dict[str, OperatorConfig]]:
    """Convert the API operator dict into Presidio OperatorConfig objects."""
    if not operators:
        return None
    return {
        entity_type: OperatorConfig(
            operator_name=cfg.get("type", "replace"),
            params=cfg.get("params") or {},
        )
        for entity_type, cfg in operators.items()
    }


def anonymize_text(
    text: str,
    analyzer_results: List[RecognizerResult],
    operators: Optional[Dict[str, Dict[str, Any]]] = None,
) -> EngineResult:
    """Anonymize *text* using the pre-computed *analyzer_results*."""
    engine = get_engine()
    operator_configs = _build_operator_configs(operators)
    return engine.anonymize(
        text=text,
        analyzer_results=analyzer_results,
        operators=operator_configs,
    )

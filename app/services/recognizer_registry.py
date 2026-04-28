from __future__ import annotations

from typing import Dict, List, Optional

from presidio_analyzer import PatternRecognizer
from presidio_analyzer.pattern import Pattern

from app.services.analyzer import get_engine

# Maps recognizer name -> (recognizer instance, type string) for custom entries
_custom: Dict[str, tuple[PatternRecognizer, str]] = {}


def add_recognizer(
    name: str,
    supported_entity: str,
    supported_language: str,
    recognizer_type: str,
    patterns: Optional[List[dict]] = None,
    deny_list: Optional[List[str]] = None,
    context: Optional[List[str]] = None,
) -> None:
    """Register a custom *PatternRecognizer* with the shared AnalyzerEngine."""
    engine = get_engine()

    if recognizer_type == "pattern":
        pattern_objects = [
            Pattern(name=p["name"], regex=p["regex"], score=p["score"])
            for p in (patterns or [])
        ]
        recognizer = PatternRecognizer(
            supported_entity=supported_entity,
            supported_language=supported_language,
            patterns=pattern_objects,
            context=context,
            name=name,
        )
    else:  # deny_list
        recognizer = PatternRecognizer(
            supported_entity=supported_entity,
            supported_language=supported_language,
            deny_list=deny_list or [],
            context=context,
            name=name,
        )

    # Replace existing recognizer with the same name if present
    if name in _custom:
        engine.registry.remove_recognizer(name)

    engine.registry.add_recognizer(recognizer)
    _custom[name] = (recognizer, recognizer_type)


def remove_recognizer(name: str) -> bool:
    """Remove a custom recognizer by *name*. Returns False when not found."""
    if name not in _custom:
        return False
    engine = get_engine()
    engine.registry.remove_recognizer(name)
    del _custom[name]
    return True


def list_custom_recognizers() -> List[dict]:
    """Return metadata for all registered custom recognizers."""
    return [
        {
            "name": recognizer.name,
            "supported_entities": recognizer.supported_entities,
            "supported_language": recognizer.supported_language,
            "type": rtype,
        }
        for recognizer, rtype in _custom.values()
    ]


def list_all_recognizers() -> List[dict]:
    """Return metadata for every recognizer currently loaded in the engine."""
    engine = get_engine()
    return [
        {
            "name": r.name,
            "supported_entities": r.supported_entities,
            "supported_language": r.supported_language,
            "is_custom": r.name in _custom,
        }
        for r in engine.registry.recognizers
    ]

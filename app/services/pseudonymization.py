"""Deterministic and reversible pseudonymization with HMAC-SHA256 (ISO 25237:2017)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Dict, List, Tuple

from presidio_analyzer import RecognizerResult

_DEFAULT_KEY: str = os.getenv("PSEUDONYMIZATION_KEY", "change-me-in-production-32bytes!")


def _make_pseudonym(value: str, entity_type: str, key: str) -> str:
    """Generate a deterministic pseudonym token for a given value and entity type."""
    raw = f"{entity_type}\x00{value}".encode("utf-8")
    digest = hmac.new(key.encode("utf-8"), raw, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(digest[:12]).decode("ascii").rstrip("=")
    return f"[{entity_type}_{token}]"


def pseudonymize_text(
    text: str,
    analyzer_results: List[RecognizerResult],
    key: str = _DEFAULT_KEY,
) -> Tuple[str, Dict[str, str]]:
    """Replace detected entities with deterministic pseudonym tokens.

    Args:
        text: Original input text.
        analyzer_results: Presidio analyzer results for the text.
        key: HMAC key used for pseudonym generation.

    Returns:
        A tuple of (pseudonymized_text, pseudonym_map) where pseudonym_map maps
        each pseudonym token to its original value.
    """
    # Sort results by start position descending to avoid offset shifts
    sorted_results = sorted(analyzer_results, key=lambda r: r.start, reverse=True)

    pseudonym_map: Dict[str, str] = {}
    result_text = text

    for entity in sorted_results:
        original_value = text[entity.start : entity.end]
        pseudonym = _make_pseudonym(original_value, entity.entity_type, key)
        pseudonym_map[pseudonym] = original_value
        result_text = result_text[: entity.start] + pseudonym + result_text[entity.end :]

    return result_text, pseudonym_map


def depseudonymize_text(pseudonymized_text: str, pseudonym_map: Dict[str, str]) -> str:
    """Reverse pseudonymization using the provided token-to-value map.

    Args:
        pseudonymized_text: Text containing pseudonym tokens.
        pseudonym_map: Mapping of pseudonym tokens to original values.

    Returns:
        Text with all pseudonym tokens replaced by their original values.
    """
    result = pseudonymized_text
    for pseudonym, original in pseudonym_map.items():
        result = result.replace(pseudonym, original)
    return result

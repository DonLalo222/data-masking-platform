"""Utilities for Chilean geographic entity recognition.

Provides accent-insensitive matching so that, e.g., 'Biobio' and 'Biobío'
are both detected as CL_REGION, while returned offsets always point to the
correct span in the *original* (unmodified) input text.

Normalisation strategy
----------------------
Input text is normalised via NFD decomposition followed by stripping of
Unicode combining marks (category "Mn").  Because every accented character
is composed of exactly one base character plus one or more combining marks
this produces a 1-to-1 character mapping, keeping the normalised string the
same length as the original.  Offset arithmetic on the normalised copy is
therefore valid for the original text as long as the input is in NFC (which
is standard for text from keyboards, web forms and databases).
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

from presidio_analyzer import AnalysisExplanation, EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_DATA_FILE = Path(__file__).parent.parent / "data" / "chile_communes.json"


def _load_chile_geo() -> dict:
    with _DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def strip_accents(text: str) -> str:
    """Return *text* with all accented characters replaced by their ASCII base
    equivalents, lowercased.

    The output is the same length as the input so offsets are preserved.
    """
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower()


# ---------------------------------------------------------------------------
# Canonical lists (exported for use by recognizers)
# ---------------------------------------------------------------------------

def get_all_region_aliases() -> List[str]:
    """Return every region alias (canonical name + all listed variants)."""
    data = _load_chile_geo()
    aliases: List[str] = []
    for region in data["regions"]:
        aliases.extend(region.get("aliases", []))
        # Also add the canonical name to be safe
        canonical = region["name"]
        if canonical not in aliases:
            aliases.append(canonical)
    # Deduplicate preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for a in aliases:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique


def get_all_communes() -> List[str]:
    """Return every commune name from all Chilean regions."""
    data = _load_chile_geo()
    communes: List[str] = []
    seen: set[str] = set()
    for region in data["regions"]:
        for c in region.get("communes", []):
            if c not in seen:
                seen.add(c)
                communes.append(c)
    return communes


# ---------------------------------------------------------------------------
# Accent-insensitive recognizer
# ---------------------------------------------------------------------------

_CONTEXT_WINDOW_CHARS = 120


class ClAccentInsensitiveRecognizer(EntityRecognizer):
    """Presidio-compatible recognizer that matches deny-list entries regardless
    of whether accented or non-accented variants are used in the input text.

    Parameters
    ----------
    supported_entity:
        The Presidio entity type string (e.g. ``"CL_REGION"``).
    name:
        Unique name used for registration / idempotent re-registration.
    deny_list:
        List of canonical strings to detect.
    context:
        Optional list of context words that, when found near a match, boost
        the confidence score by ``context_boost``.
    base_score:
        Base confidence score returned for each match.
    context_boost:
        Amount added to *base_score* when a context word is found nearby.
    accent_insensitive:
        When ``True`` (default), both the deny-list entries and the input text
        are normalised before comparison so accents do not affect matching.
    """

    DEFAULT_SCORE: float = 0.85
    DEFAULT_CONTEXT_BOOST: float = 0.10

    def __init__(
        self,
        supported_entity: str,
        name: str,
        deny_list: List[str],
        context: Optional[List[str]] = None,
        base_score: float = DEFAULT_SCORE,
        context_boost: float = DEFAULT_CONTEXT_BOOST,
        accent_insensitive: bool = True,
    ) -> None:
        super().__init__(
            supported_entities=[supported_entity],
            name=name,
            supported_language="es",
        )
        self.deny_list = deny_list
        self.context = context or []
        self.base_score = base_score
        self.context_boost = context_boost
        self.accent_insensitive = accent_insensitive

        # Pre-compile one regex per deny-list entry operating on normalised text.
        # Each tuple is (compiled_pattern, original_entry_for_explanation).
        self._compiled: List[tuple] = []
        for entry in deny_list:
            normalised = strip_accents(entry) if accent_insensitive else entry.lower()
            # \b anchors work correctly on ASCII-only normalised text.
            pattern = re.compile(
                r"\b" + re.escape(normalised) + r"\b", re.IGNORECASE
            )
            self._compiled.append((pattern, entry))

        # Normalised context words for fast window search.
        self._norm_context = [strip_accents(w) for w in self.context]

    # ------------------------------------------------------------------
    # EntityRecognizer interface
    # ------------------------------------------------------------------

    def load(self) -> None:  # required abstract method
        pass

    def analyze(
        self,
        text: str,
        entities: List[str],
        nlp_artifacts: Optional[NlpArtifacts] = None,
    ) -> List[RecognizerResult]:
        if self.supported_entities[0] not in entities:
            return []

        search_text = strip_accents(text) if self.accent_insensitive else text.lower()
        results: List[RecognizerResult] = []

        for pattern, original_entry in self._compiled:
            for match in pattern.finditer(search_text):
                score = self.base_score

                # Context boost: look for context words in surrounding window.
                if self._norm_context:
                    win_start = max(0, match.start() - _CONTEXT_WINDOW_CHARS)
                    win_end = min(
                        len(search_text), match.end() + _CONTEXT_WINDOW_CHARS
                    )
                    window = search_text[win_start:win_end]
                    if any(cw in window for cw in self._norm_context):
                        score = min(1.0, score + self.context_boost)

                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=score,
                    textual_explanation=(
                        f"Matched deny-list entry '{original_entry}' "
                        f"(accent-insensitive={self.accent_insensitive})"
                    ),
                )
                results.append(
                    RecognizerResult(
                        entity_type=self.supported_entities[0],
                        start=match.start(),
                        end=match.end(),
                        score=score,
                        analysis_explanation=explanation,
                        recognition_metadata={
                            RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                            RecognizerResult.RECOGNIZER_NAME_KEY: self.name,
                        },
                    )
                )

        # Remove exact duplicates that may arise from overlapping patterns.
        return _dedup(results)


def _dedup(results: List[RecognizerResult]) -> List[RecognizerResult]:
    """Remove duplicate results with identical (start, end, entity_type)."""
    seen: set[tuple] = set()
    unique: List[RecognizerResult] = []
    for r in results:
        key = (r.start, r.end, r.entity_type)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique

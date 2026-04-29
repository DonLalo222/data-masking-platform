"""Audit trail for ISO 29101 — in-memory store with structured logging."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

_store: Deque[Dict[str, Any]] = deque(maxlen=10_000)
_logger = logging.getLogger("data_masking.audit")


def record(
    *,
    operation: str,
    language: str,
    framework: str,
    entities_found: List[str],
    operators_applied: List[str],
    input_length: int,
    risk_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create an audit entry, store it and log it.

    Args:
        operation: Name of the operation performed (e.g. ``"anonymize"``).
        language: BCP-47 language code used for analysis.
        framework: Compliance framework identifier (e.g. ``"hipaa-safe-harbor"``).
        entities_found: List of entity types detected in the input.
        operators_applied: List of operator names applied.
        input_length: Character length of the input text.
        risk_score: Optional re-identification risk score.
        metadata: Optional additional metadata dict.

    Returns:
        The audit entry dict that was stored.
    """
    entry: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "language": language,
        "framework": framework,
        "entities_found": entities_found,
        "operators_applied": operators_applied,
        "input_length": input_length,
        "risk_score": risk_score,
        "metadata": metadata or {},
    }
    _store.append(entry)
    _logger.info(
        "audit",
        extra={
            "framework": framework,
            "operation": operation,
            "entities_count": len(entities_found),
            "risk_score": risk_score,
        },
    )
    return entry


def get_entries(
    limit: int = 100,
    framework: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return the most recent audit entries, optionally filtered by framework.

    Args:
        limit: Maximum number of entries to return.
        framework: If provided, only return entries for this framework.

    Returns:
        List of audit entry dicts, most recent last.
    """
    entries = list(_store)
    if framework is not None:
        entries = [e for e in entries if e.get("framework") == framework]
    return entries[-limit:]


def clear() -> None:
    """Clear all stored audit entries (useful in tests)."""
    _store.clear()

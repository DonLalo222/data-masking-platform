from __future__ import annotations

from typing import Any


def generalize(value: Any, bucket_size: int = 10) -> str:
    """Generalize a numeric value into a range bucket.

    Examples:
        generalize(34, 10)  → "30-40"
        generalize(100, 25) → "100-125"
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    lower = int(num // bucket_size) * bucket_size
    upper = lower + bucket_size
    return f"{lower}-{upper}"

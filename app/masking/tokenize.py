from __future__ import annotations

import hashlib
from typing import Any


def tokenize(value: Any) -> str:
    """Replace with a deterministic token: ``tok_`` + first 8 hex chars of SHA-256."""
    digest = hashlib.sha256(str(value).encode()).hexdigest()
    return f"tok_{digest[:8]}"

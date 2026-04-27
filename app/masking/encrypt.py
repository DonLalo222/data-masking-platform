from __future__ import annotations

import hashlib
from typing import Any


def encrypt(value: Any) -> str:
    """Replace with the SHA-256 hex digest of the value."""
    return hashlib.sha256(str(value).encode()).hexdigest()

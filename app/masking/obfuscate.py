from __future__ import annotations

import re
from typing import Any


def obfuscate(value: Any) -> str:
    """Partially mask the value.

    - Email  : ``user@mail.com``  → ``u***@****.com``
    - Default: mask all but the last 4 characters, e.g. ``****1234``
    """
    str_value = str(value)

    if re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", str_value):
        local, domain = str_value.split("@", 1)
        masked_local = local[0] + "***" if len(local) > 1 else "***"
        domain_parts = domain.rsplit(".", 1)
        masked_domain = "*" * len(domain_parts[0])
        ext = domain_parts[1] if len(domain_parts) > 1 else ""
        return f"{masked_local}@{masked_domain}.{ext}"

    if len(str_value) <= 4:
        return "*" * len(str_value)

    return "*" * (len(str_value) - 4) + str_value[-4:]

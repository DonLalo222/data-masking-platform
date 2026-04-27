from __future__ import annotations

import hashlib
from typing import Any


def pseudonymize(value: Any) -> str:
    """Replace with consistent fake data using Faker.

    The same input always produces the same fake output because the Faker
    seed is derived from a SHA-256 hash of the original value.
    """
    from faker import Faker

    str_value = str(value)
    seed = int(hashlib.sha256(str_value.encode()).hexdigest(), 16) % (2**32)

    fake = Faker()
    fake.seed_instance(seed)

    lower = str_value.lower()

    if "@" in lower:
        return fake.email()
    if any(kw in lower for kw in ("phone", "tel", "mobile", "celular", "telefono")):
        return fake.phone_number()
    if any(kw in lower for kw in ("date", "fecha", "birth", "nacimiento")):
        return str(fake.date())
    if any(kw in lower for kw in ("address", "direccion", "street", "calle")):
        return fake.address().replace("\n", ", ")
    if any(kw in lower for kw in ("city", "ciudad")):
        return fake.city()
    if any(kw in lower for kw in ("country", "pais")):
        return fake.country()
    if any(kw in lower for kw in ("company", "empresa")):
        return fake.company()
    if str_value.replace(".", "").replace("-", "").isdigit():
        return str(fake.random_int(min=1, max=9999))

    return fake.name()

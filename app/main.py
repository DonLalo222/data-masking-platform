from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routers import analyze, anonymize, compliance, recognizers
from app.services.clinical_recognizers_cl import register_clinical_recognizers_cl
from app.services.clinical_recognizers_es import register_clinical_recognizers_es


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if config.ENABLE_CLINICAL_ES:
        register_clinical_recognizers_es()
    if config.ENABLE_CLINICAL_CL:
        register_clinical_recognizers_cl()
    yield

_DESCRIPTION = """
## Data Masking Platform API

A REST API for detecting and masking **Personally Identifiable Information (PII)**,
powered by [Microsoft Presidio](https://microsoft.github.io/presidio/).

---

### Core features

| Feature | Description |
|---------|-------------|
| **PII detection** | Identify 50+ entity types — names, e-mails, phones, SSNs, credit cards, IBANs, IP addresses and more |
| **Flexible masking** | Choose a different anonymization strategy for each entity type |
| **Custom recognizers** | Add regex or deny-list recognizers at runtime without restarting |
| **Batch processing** | Anonymize many texts in a single request |
| **Multi-language** | Supports every language covered by the underlying spaCy model |
| **Compliance frameworks** | Pre-built profiles for HIPAA, MINSAL Chile, ISO 25237 and ISO 29101 |

---

### Anonymization operators

| Operator | Description | Key parameters |
|----------|-------------|----------------|
| `replace` | Substitute with a fixed string | `new_value` (default: `<ENTITY_TYPE>`) |
| `redact` | Remove the entity entirely | — |
| `hash` | Replace with a digest | `hash_type`: `md5` · `sha256` (default) · `sha512` |
| `encrypt` | AES-CBC encryption | `key`: 16-byte base64-encoded string |
| `mask` | Overwrite characters | `masking_char`, `chars_to_mask`, `from_end` |
| `keep` | Preserve the original value | — |

Per-entity overrides go in the `operators` map; use the `DEFAULT` key as a fallback
for every entity type not explicitly listed.

---

### Compliance frameworks

| Framework | Endpoint | Description |
|-----------|----------|-------------|
| HIPAA Safe Harbor | `POST /compliance/hipaa/safe-harbor` | Removes all 18 PHI categories |
| HIPAA Expert Determination | `POST /compliance/hipaa/expert-determination` | Re-identification risk scoring |
| MINSAL Chile / Ley 19.628 | `POST /compliance/minsal` | Chilean clinical data anonymization |
| ISO 25237 Pseudonymization | `POST /compliance/iso25237/pseudonymize` | HMAC-SHA256 pseudonymization |
| ISO 29101 Audit Trail | `GET /compliance/audit-log` | Audit log of all PII operations |
"""

app = FastAPI(
    title="Data Masking Platform",
    description=_DESCRIPTION,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(anonymize.router)
app.include_router(recognizers.router)
app.include_router(compliance.router)


@app.get("/", tags=["Health"])
def root() -> dict:
    return {"status": "ok", "service": "Data Masking Platform", "version": "3.0.0"}

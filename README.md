# Data Masking Platform

A Python REST API for detecting and masking **Personally Identifiable Information (PII)**, powered by [Microsoft Presidio](https://microsoft.github.io/presidio/).

Interactive API docs are available at **`/docs`** (Swagger UI) and **`/redoc`** (ReDoc) once the service is running.

---

## Features

| Feature | Details |
|---------|---------|
| **PII detection** | 50+ entity types — names, e-mails, phones, credit cards, IBANs, IP addresses, SSNs and more |
| **Flexible masking** | Six anonymization strategies, configurable per entity type |
| **Custom recognizers** | Add regex or deny-list recognizers at runtime via the API |
| **Batch processing** | Anonymize many texts in one request |
| **Multi-language** | Any language supported by the underlying spaCy model |
| **Spanish clinical entities** | Built-in recognizers for ES_DNI, ES_NIE, ES_TARJETA_SANITARIA and more |
| **Chilean ID entities** | Built-in recognizers for CL_RUN, CL_PASAPORTE, CL_CEDULA_EXTRANJERIA, CL_LICENCIA_CONDUCIR, CL_PHONE |
| **Swagger / OpenAPI** | Full documentation built in at `/docs` |

---

## Anonymization operators

| Operator | Description | Parameters |
|----------|-------------|------------|
| `replace` | Substitute with a fixed string | `new_value` (default: `<ENTITY_TYPE>`) |
| `redact` | Remove the entity entirely | — |
| `hash` | Replace with a digest | `hash_type`: `md5` · `sha256` (default) · `sha512` |
| `encrypt` | AES-CBC encryption | `key`: 16-byte base64-encoded key |
| `mask` | Overwrite N characters | `masking_char`, `chars_to_mask`, `from_end` |
| `keep` | Preserve the original value | — |

Specify per-entity overrides in the `operators` map; use the `DEFAULT` key as a catch-all fallback.

---

## Quick start

### Local (Python 3.11+)

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
python -m spacy download es_core_news_lg
uvicorn app.main:app --reload
```

Open <http://localhost:8000/docs> for the interactive Swagger UI.

### Docker

```bash
docker compose up --build
```

---

## API reference

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |

### Analysis

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Detect PII entities in text |
| POST | `/analyze/batch` | Detect PII entities in a list of texts |
| GET | `/analyze/entities` | List all supported entity types |

### Anonymization

| Method | Path | Description |
|--------|------|-------------|
| POST | `/anonymize` | Anonymize PII in a single text |
| POST | `/anonymize/batch` | Anonymize a list of texts |

### Custom recognizers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/recognizers` | List all recognizers (built-in + custom) |
| POST | `/recognizers` | Add a custom recognizer |
| DELETE | `/recognizers/{name}` | Remove a custom recognizer |

---

## Usage examples

### Detect PII

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, my name is John Smith and my e-mail is john@example.com",
    "language": "en"
  }'
```

### Anonymize with custom operators

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello John Smith, contact me at john@example.com",
    "language": "en",
    "operators": {
      "PERSON":        { "type": "replace", "params": { "new_value": "[NAME]" } },
      "EMAIL_ADDRESS": { "type": "mask",    "params": { "masking_char": "*", "chars_to_mask": 10, "from_end": false } },
      "DEFAULT":       { "type": "redact" }
    }
  }'
```

### Add a custom regex recognizer

```bash
curl -X POST http://localhost:8000/recognizers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "employee_id_recognizer",
    "supported_entity": "EMPLOYEE_ID",
    "supported_language": "en",
    "type": "pattern",
    "patterns": [
      { "name": "emp_id", "regex": "EMP\\d{6}", "score": 0.9 }
    ],
    "context": ["employee", "staff", "id"]
  }'
```

### Add a deny-list recognizer

```bash
curl -X POST http://localhost:8000/recognizers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "codename_recognizer",
    "supported_entity": "PROJECT_CODENAME",
    "supported_language": "en",
    "type": "deny_list",
    "deny_list": ["Project Alpha", "Project Beta", "Project Gamma"]
  }'
```

---

## Spanish language & clinical recognizers

The platform includes built-in support for **Spanish (es)** using the `es_core_news_lg` spaCy model, with specialized pattern recognizers aligned with ISO, CIE-10 and HL7 standards.

### Available clinical entities

| Entity | Standard | Description | Example |
|--------|----------|-------------|---------|
| `ES_DNI` | ISO/IEC 7812 | Spanish national ID (8 digits + letter) | `12345678Z` |
| `ES_NIE` | ISO/IEC 7812 | Foreigner ID (X/Y/Z + 7 digits + letter) | `X1234567L` |
| `ES_TARJETA_SANITARIA` | ISO 27799 | Health card number CIP/SNS (4 letters + 8 digits) | `ABCD12345678` |
| `ES_NUHSA` | HL7 / ISO 27799 | Clinical record number (AN + 10 digits) | `AN0123456789` |
| `ES_CIE10_CODE` | CIE-10 / ICD-10 | Diagnostic code | `J18.9` |
| `ES_PHONE_NUMBER` | E.164 | Spanish phone number | `+34612345678` |
| `ES_POSTAL_CODE` | ISO 3166 | Spanish postal code | `28001` |
| `PERSON` | ISO 29101 | Patient names detected by the spaCy NER model | `María García` |

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CLINICAL_ES` | `true` | Enable/disable Spanish clinical recognizers on startup |

### Usage examples

#### Detect a DNI

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "El paciente con DNI 12345678Z fue ingresado el lunes.",
    "language": "es",
    "entities": ["ES_DNI"]
  }'
```

#### Detect a CIE-10 diagnostic code

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Diagnóstico principal: J18.9 (Neumonía no especificada).",
    "language": "es",
    "entities": ["ES_CIE10_CODE"]
  }'
```

#### Anonymize a full clinical note in Spanish

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Paciente María García, DNI 12345678Z, tarjeta sanitaria ABCD12345678. Diagnóstico J18.9. Teléfono: 612345678.",
    "language": "es",
    "operators": {
      "PERSON":                 { "type": "replace", "params": { "new_value": "[PACIENTE]" } },
      "ES_DNI":                 { "type": "redact" },
      "ES_TARJETA_SANITARIA":   { "type": "redact" },
      "ES_CIE10_CODE":          { "type": "replace", "params": { "new_value": "[DIAGNÓSTICO]" } },
      "ES_PHONE_NUMBER":        { "type": "mask", "params": { "masking_char": "*", "chars_to_mask": 6, "from_end": true } },
      "DEFAULT":                { "type": "replace" }
    }
  }'
```

---

## Chilean identification document recognizers

The platform includes built-in support for **Chilean (es)** identification documents.

### Available Chilean entities

| Entity | Description | Example |
|--------|-------------|---------|
| `CL_RUN` | RUN/RUT chileno with check digit (including K) | `12.345.678-9` |
| `CL_PASAPORTE` | Chilean passport — 1-2 letters + 6-7 digits | `A1234567` |
| `CL_CEDULA_EXTRANJERIA` | Foreigner identity card — PE + 7 digits | `PE1234567` |
| `CL_LICENCIA_CONDUCIR` | Chilean driver's licence — letter + 7 digits | `B1234567` |
| `CL_PHONE` | Chilean phone number (+56 / local) | `+56 9 1234 5678` |

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CHILE` | `true` | Enable/disable Chilean identification recognizers on startup |

### Usage examples

#### Detect a RUT and phone number

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "El RUT del paciente es 12.345.678-9 y su teléfono es +56 9 1234 5678",
    "language": "es",
    "entities": ["CL_RUN", "CL_PHONE"]
  }'
```

#### Anonymize a Chilean clinical note

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Paciente Juan Pérez, RUT 12.345.678-9, pasaporte A1234567. Teléfono: +56912345678.",
    "language": "es",
    "operators": {
      "PERSON":               { "type": "replace", "params": { "new_value": "[PACIENTE]" } },
      "CL_RUN":               { "type": "redact" },
      "CL_PASAPORTE":         { "type": "redact" },
      "CL_PHONE":             { "type": "mask", "params": { "masking_char": "*", "chars_to_mask": 6, "from_end": true } },
      "DEFAULT":              { "type": "replace" }
    }
  }'
```

---

Environment variables (override in `docker-compose.yml` or your shell):

| Variable | Default | Description |
|----------|---------|-------------|
| `NLP_ENGINE_MODEL` | `en_core_web_lg` | spaCy model used by Presidio (English) |
| `DEFAULT_LANGUAGE` | `en` | BCP-47 language code |
| `DEFAULT_SCORE_THRESHOLD` | `0.5` | Minimum confidence score |
| `ENABLE_CLINICAL_ES` | `true` | Enable Spanish clinical recognizers (ISO/CIE-10/HL7) |
| `ENABLE_CHILE` | `true` | Enable Chilean identification document recognizers |

---

## Running tests

```bash
python -m pytest tests/ -v
```

---

## Project structure

```
app/
├── main.py                     # FastAPI application entry point
├── config.py                   # Environment-based configuration
├── routers/
│   ├── analyze.py              # /analyze endpoints
│   ├── anonymize.py            # /anonymize endpoints
│   └── recognizers.py         # /recognizers endpoints
├── models/
│   ├── analyze.py              # Pydantic request/response models
│   ├── anonymize.py
│   └── recognizer.py
└── services/
    ├── analyzer.py             # Presidio AnalyzerEngine wrapper (en + es)
    ├── anonymizer.py           # Presidio AnonymizerEngine wrapper
    ├── chile_recognizers.py    # Chilean identification document recognizers
    ├── clinical_recognizers_es.py  # Spanish clinical recognizers (ISO/CIE-10/HL7)
    └── recognizer_registry.py # Custom recognizer management
tests/
├── test_analyze.py
├── test_anonymize.py
├── test_chile_recognizers.py   # Chilean identification recognizer tests
├── test_clinical_es.py         # Spanish clinical recognizer tests
└── test_recognizers.py
```

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

## Configuration

Environment variables (override in `docker-compose.yml` or your shell):

| Variable | Default | Description |
|----------|---------|-------------|
| `NLP_ENGINE_MODEL` | `en_core_web_lg` | spaCy model used by Presidio |
| `DEFAULT_LANGUAGE` | `en` | BCP-47 language code |
| `DEFAULT_SCORE_THRESHOLD` | `0.5` | Minimum confidence score |

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
    ├── analyzer.py             # Presidio AnalyzerEngine wrapper
    ├── anonymizer.py           # Presidio AnonymizerEngine wrapper
    └── recognizer_registry.py # Custom recognizer management
tests/
├── test_analyze.py
├── test_anonymize.py
└── test_recognizers.py
```

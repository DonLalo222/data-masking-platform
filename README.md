# Data Masking Platform

A **FastAPI-based REST API** for masking sensitive data from multiple database types. Connect to PostgreSQL, MySQL, SQLite or SQL Server, configure masking rules per column, and download the masked dataset as CSV or JSON.

---

## Features

- 🔌 **Multi-DB support** — PostgreSQL, MySQL, SQLite, SQL Server
- 🔍 **Schema introspection** — discover tables and columns automatically
- 🛡️ **8 masking strategies** — anonymize, pseudonymize, obfuscate, tokenize, encrypt, generalize, shuffle, keep
- 📦 **Export** — download masked datasets as CSV or JSON
- 📄 **OpenAPI docs** — interactive docs at `/docs`

---

## Project Structure

```
data-masking-platform/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── store.py                 # In-memory storage
│   ├── connector_factory.py     # Connector factory
│   ├── routers/
│   │   ├── connections.py       # CRUD for DB connections
│   │   ├── schemas.py           # Schema introspection
│   │   ├── rules.py             # Masking rules CRUD
│   │   └── export.py            # Export endpoint
│   ├── connectors/
│   │   ├── base.py              # Abstract base connector
│   │   ├── postgres.py
│   │   ├── mysql.py
│   │   ├── sqlite.py
│   │   └── sqlserver.py
│   ├── masking/
│   │   ├── engine.py            # Applies rules row by row
│   │   ├── anonymize.py
│   │   ├── pseudonymize.py
│   │   ├── obfuscate.py
│   │   ├── tokenize.py
│   │   ├── encrypt.py
│   │   ├── generalize.py
│   │   └── shuffle.py
│   └── models/
│       ├── connection.py
│       ├── rule.py
│       └── export.py
├── tests/
│   ├── test_connections.py
│   ├── test_masking.py
│   └── test_export.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Running with Docker

```bash
# Start the API + PostgreSQL + MySQL
docker compose up --build

# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Running Locally

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn app.main:app --reload

# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## API Usage Examples

### Health Check

```bash
curl http://localhost:8000/
```

### Connections

```bash
# Create a SQLite connection (no external DB required)
curl -X POST http://localhost:8000/connections \
  -H "Content-Type: application/json" \
  -d '{"name": "local-sqlite", "db_type": "sqlite", "database": "mydata.db"}'

# Create a PostgreSQL connection
curl -X POST http://localhost:8000/connections \
  -H "Content-Type: application/json" \
  -d '{"name": "prod-pg", "db_type": "postgres", "host": "localhost", "port": 5432, "database": "mydb", "username": "user", "password": "pass"}'

# List all connections
curl http://localhost:8000/connections

# Get a connection by ID
curl http://localhost:8000/connections/{id}

# Test a connection
curl -X POST http://localhost:8000/connections/{id}/test

# Delete a connection
curl -X DELETE http://localhost:8000/connections/{id}
```

### Schema Introspection

```bash
# List tables
curl http://localhost:8000/connections/{id}/schema/tables

# List columns for a table
curl http://localhost:8000/connections/{id}/schema/tables/users/columns
```

### Masking Rules

```bash
# Create a masking profile
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "profile_users",
    "connection_id": "{connection_id}",
    "table": "users",
    "column_rules": [
      {"column": "id",    "strategy": "keep",        "options": {}},
      {"column": "name",  "strategy": "pseudonymize", "options": {}},
      {"column": "email", "strategy": "obfuscate",    "options": {}},
      {"column": "age",   "strategy": "generalize",   "options": {"bucket_size": 10}}
    ]
  }'

# List all rules
curl http://localhost:8000/rules

# Get a rule
curl http://localhost:8000/rules/{id}

# Update a rule
curl -X PUT http://localhost:8000/rules/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "updated-profile"}'

# Delete a rule
curl -X DELETE http://localhost:8000/rules/{id}
```

### Export

```bash
# Export as CSV (download)
curl -X POST http://localhost:8000/export \
  -H "Content-Type: application/json" \
  -d '{"rule_id": "{rule_id}", "format": "csv", "limit": 1000}' \
  --output masked_data.csv

# Export as JSON
curl -X POST http://localhost:8000/export \
  -H "Content-Type: application/json" \
  -d '{"rule_id": "{rule_id}", "format": "json", "limit": 1000}'
```

---

## Supported DB Types

| DB Type | `db_type` value | Driver |
|---------|-----------------|--------|
| PostgreSQL | `postgres` | psycopg2 |
| MySQL / MariaDB | `mysql` | pymysql |
| SQLite | `sqlite` | sqlite3 (built-in) |
| SQL Server | `sqlserver` | pyodbc |

---

## Masking Strategies

| Strategy | `strategy` value | Behavior |
|----------|-----------------|----------|
| Keep | `keep` | Return value unchanged |
| Anonymize | `anonymize` | Replace with `null` |
| Pseudonymize | `pseudonymize` | Replace with consistent fake data (Faker, deterministic seed) |
| Obfuscate | `obfuscate` | Mask middle characters — `****1234`, `u***@****.com` |
| Tokenize | `tokenize` | `tok_` + first 8 chars of SHA-256 hash |
| Encrypt | `encrypt` | Full SHA-256 hex digest |
| Generalize | `generalize` | Numeric bucket — `34` → `"30-40"` (configurable `bucket_size`) |
| Shuffle | `shuffle` | Shuffle column values across rows |

### `generalize` options

| Option | Default | Description |
|--------|---------|-------------|
| `bucket_size` | `10` | Size of each numeric range bucket |


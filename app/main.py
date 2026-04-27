from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import connections, schemas, rules, export

app = FastAPI(
    title="Data Masking Platform",
    description="REST API for connecting to databases, configuring masking rules and exporting masked datasets.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connections.router)
app.include_router(schemas.router)
app.include_router(rules.router)
app.include_router(export.router)


@app.get("/", tags=["health"])
def root() -> dict:
    return {"status": "ok", "message": "Data Masking Platform API is running"}

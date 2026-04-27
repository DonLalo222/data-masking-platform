from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.store import connections
from app.connector_factory import get_connector

router = APIRouter(prefix="/connections", tags=["schema"])


@router.get("/{conn_id}/schema/tables", response_model=List[str])
def list_tables(conn_id: str) -> List[str]:
    conn = connections.get(conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        connector = get_connector(conn)
        tables = connector.get_tables()
        connector.close()
        return tables
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{conn_id}/schema/tables/{table}/columns", response_model=List[Dict[str, Any]])
def list_columns(conn_id: str, table: str) -> List[Dict[str, Any]]:
    conn = connections.get(conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        connector = get_connector(conn)
        columns = connector.get_columns(table)
        connector.close()
        return columns
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

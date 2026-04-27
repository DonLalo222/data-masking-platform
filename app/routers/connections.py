from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.models.connection import ConnectionCreate, ConnectionResponse
from app.store import connections
from app.connector_factory import get_connector

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(payload: ConnectionCreate) -> ConnectionResponse:
    conn_id = str(uuid.uuid4())
    conn_data = payload.model_dump()
    conn_data["id"] = conn_id
    connections[conn_id] = conn_data
    return ConnectionResponse(**conn_data)


@router.get("", response_model=List[ConnectionResponse])
def list_connections() -> List[ConnectionResponse]:
    return [ConnectionResponse(**c) for c in connections.values()]


@router.get("/{conn_id}", response_model=ConnectionResponse)
def get_connection(conn_id: str) -> ConnectionResponse:
    conn = connections.get(conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return ConnectionResponse(**conn)


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_connection(conn_id: str) -> Response:
    if conn_id not in connections:
        raise HTTPException(status_code=404, detail="Connection not found")
    del connections[conn_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{conn_id}/test")
def test_connection(conn_id: str) -> dict:
    conn = connections.get(conn_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        connector = get_connector(conn)
        reachable = connector.test_connection()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not reachable:
        raise HTTPException(status_code=400, detail="Connection test failed")
    return {"status": "ok", "message": "Connection successful"}

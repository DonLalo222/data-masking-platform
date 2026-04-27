from __future__ import annotations

import csv
import io
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.export import ExportRequest
from app.models.rule import ColumnRule
from app.store import connections, rules
from app.connector_factory import get_connector
from app.masking.engine import apply_masking

router = APIRouter(prefix="/export", tags=["export"])


@router.post("")
def export_data(payload: ExportRequest):
    rule = rules.get(payload.rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    conn = connections.get(rule["connection_id"])
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        connector = get_connector(conn)
        raw_rows: List[Dict[str, Any]] = connector.fetch_data(rule["table"], payload.limit)
        connector.close()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    column_rules: List[ColumnRule] = [ColumnRule(**cr) for cr in rule["column_rules"]]
    masked_rows = apply_masking(raw_rows, column_rules)

    if payload.format == "json":
        return JSONResponse(content=masked_rows)

    output = io.StringIO()
    if masked_rows:
        writer = csv.DictWriter(output, fieldnames=list(masked_rows[0].keys()))
        writer.writeheader()
        writer.writerows(masked_rows)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=masked_data.csv"},
    )

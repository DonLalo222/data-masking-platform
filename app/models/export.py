from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    rule_id: str
    format: Literal["csv", "json"] = "csv"
    limit: int = Field(default=1000, ge=1, le=100000)

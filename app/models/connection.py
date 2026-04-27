from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class DBType(str, Enum):
    postgres = "postgres"
    mysql = "mysql"
    sqlite = "sqlite"
    sqlserver = "sqlserver"


class ConnectionCreate(BaseModel):
    name: str
    db_type: DBType
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: DBType
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None

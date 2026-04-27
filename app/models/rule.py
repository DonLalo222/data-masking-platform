from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from enum import Enum


class MaskingStrategy(str, Enum):
    keep = "keep"
    anonymize = "anonymize"
    pseudonymize = "pseudonymize"
    obfuscate = "obfuscate"
    tokenize = "tokenize"
    encrypt = "encrypt"
    generalize = "generalize"
    shuffle = "shuffle"


class ColumnRule(BaseModel):
    column: str
    strategy: MaskingStrategy
    options: Dict[str, Any] = {}


class RuleCreate(BaseModel):
    name: str
    connection_id: str
    table: str
    column_rules: List[ColumnRule]


class RuleResponse(BaseModel):
    id: str
    name: str
    connection_id: str
    table: str
    column_rules: List[ColumnRule]


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    connection_id: Optional[str] = None
    table: Optional[str] = None
    column_rules: Optional[List[ColumnRule]] = None

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PatternConfig(BaseModel):
    name: str = Field(..., description="Human-readable name for the pattern.")
    regex: str = Field(..., description="Regular expression that matches the entity.")
    score: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score assigned to matches.")


class RecognizerRequest(BaseModel):
    name: str = Field(..., description="Unique identifier for the recognizer.")
    supported_entity: str = Field(
        ...,
        description="Entity type this recognizer detects (e.g. `EMPLOYEE_ID`).",
    )
    supported_language: str = Field("en", description="BCP-47 language code.")
    type: Literal["pattern", "deny_list"] = Field(
        ...,
        description=(
            "Recognition strategy:\n"
            "- **pattern** – regex-based matching (requires `patterns`)\n"
            "- **deny_list** – exact string matching (requires `deny_list`)"
        ),
    )
    patterns: Optional[List[PatternConfig]] = Field(
        None, description="Regex patterns (required when `type` is `pattern`)."
    )
    deny_list: Optional[List[str]] = Field(
        None, description="Exact strings to match (required when `type` is `deny_list`)."
    )
    context: Optional[List[str]] = Field(
        None,
        description="Context words that boost the confidence score when found near a match.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "employee_id_recognizer",
                "supported_entity": "EMPLOYEE_ID",
                "supported_language": "en",
                "type": "pattern",
                "patterns": [{"name": "emp_id", "regex": r"EMP\d{6}", "score": 0.9}],
                "context": ["employee", "staff", "id"],
            }
        }
    }


class RecognizerInfo(BaseModel):
    name: str
    supported_entities: List[str]
    supported_language: str
    is_custom: bool = Field(False, description="True when this recognizer was added via the API.")

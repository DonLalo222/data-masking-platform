from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Text to scan for PII entities.")
    language: str = Field("en", description="BCP-47 language code (e.g. 'en', 'es').")
    entities: Optional[List[str]] = Field(
        None,
        description="Limit detection to these entity types. Omit to detect all supported types.",
    )
    score_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0–1) for a detection to be returned.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Hello, my name is John Smith and my e-mail is john@example.com",
                "language": "en",
                "entities": ["PERSON", "EMAIL_ADDRESS"],
                "score_threshold": 0.5,
            }
        }
    }


class EntityResult(BaseModel):
    entity_type: str = Field(..., description="Detected entity type (e.g. PERSON).")
    start: int = Field(..., description="Start character index in the original text.")
    end: int = Field(..., description="End character index (exclusive) in the original text.")
    score: float = Field(..., description="Confidence score of the detection.")
    text: str = Field(..., description="Matched substring from the original text.")


class AnalyzeResponse(BaseModel):
    entities: List[EntityResult]

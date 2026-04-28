from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

from app.models.analyze import AnalyzeRequest, AnalyzeResponse, EntityResult
from app.services import analyzer as analyzer_svc

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalyzeResponse,
    summary="Analyze text for PII entities",
    description=(
        "Scan the supplied text for Personally Identifiable Information. "
        "Returns the entity type, character offsets, confidence score, and matched text "
        "for every detected entity."
    ),
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    results = analyzer_svc.analyze_text(
        text=request.text,
        language=request.language,
        entities=request.entities,
        score_threshold=request.score_threshold,
    )
    entities = [
        EntityResult(
            entity_type=r.entity_type,
            start=r.start,
            end=r.end,
            score=r.score,
            text=request.text[r.start : r.end],
        )
        for r in results
    ]
    return AnalyzeResponse(entities=entities)


@router.get(
    "/entities",
    response_model=List[str],
    summary="List supported entity types",
    description="Return all PII entity types that can be detected for the given language.",
)
async def list_entities(
    language: str = Query("en", description="BCP-47 language code."),
) -> List[str]:
    return analyzer_svc.get_supported_entities(language=language)

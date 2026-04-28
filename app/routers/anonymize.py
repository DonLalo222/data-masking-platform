from __future__ import annotations

from fastapi import APIRouter

from app.models.anonymize import (
    AnonymizeRequest,
    AnonymizeResponse,
    AnonymizedItem,
    BatchAnonymizeRequest,
    BatchAnonymizeResponse,
)
from app.services import analyzer as analyzer_svc
from app.services import anonymizer as anonymizer_svc

router = APIRouter(prefix="/anonymize", tags=["Anonymization"])


def _do_anonymize(request: AnonymizeRequest) -> AnonymizeResponse:
    """Shared logic for single and batch anonymization."""
    analyzer_results = analyzer_svc.analyze_text(
        text=request.text,
        language=request.language,
        entities=request.entities,
        score_threshold=request.score_threshold,
    )

    operators_dict = None
    if request.operators:
        operators_dict = {
            k: {"type": v.type, "params": v.params or {}}
            for k, v in request.operators.items()
        }

    result = anonymizer_svc.anonymize_text(
        text=request.text,
        analyzer_results=analyzer_results,
        operators=operators_dict,
    )

    items = [
        AnonymizedItem(
            operator=item.operator,
            entity_type=item.entity_type,
            start=item.start,
            end=item.end,
            text=item.text,
        )
        for item in result.items
    ]
    return AnonymizeResponse(text=result.text, items=items)


@router.post(
    "",
    response_model=AnonymizeResponse,
    summary="Anonymize PII in text",
    description=(
        "Detect and anonymize all PII entities in the supplied text. "
        "You can customize the masking strategy per entity type via the `operators` field."
    ),
)
async def anonymize(request: AnonymizeRequest) -> AnonymizeResponse:
    return _do_anonymize(request)


@router.post(
    "/batch",
    response_model=BatchAnonymizeResponse,
    summary="Anonymize multiple texts",
    description="Apply the same anonymization configuration to a list of texts in one call.",
)
async def anonymize_batch(request: BatchAnonymizeRequest) -> BatchAnonymizeResponse:
    results = [
        _do_anonymize(
            AnonymizeRequest(
                text=text,
                language=request.language,
                entities=request.entities,
                score_threshold=request.score_threshold,
                operators=request.operators,
            )
        )
        for text in request.texts
    ]
    return BatchAnonymizeResponse(results=results)

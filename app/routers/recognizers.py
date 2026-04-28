from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.recognizer import RecognizerInfo, RecognizerRequest
from app.services import recognizer_registry as registry

router = APIRouter(prefix="/recognizers", tags=["Custom Recognizers"])


@router.get(
    "",
    response_model=List[RecognizerInfo],
    summary="List all recognizers",
    description=(
        "Return metadata for every recognizer loaded in the analyzer engine, "
        "including both built-in and custom recognizers."
    ),
)
async def list_recognizers() -> List[RecognizerInfo]:
    return [RecognizerInfo(**r) for r in registry.list_all_recognizers()]


@router.post(
    "",
    response_model=dict,
    status_code=201,
    summary="Add a custom recognizer",
    description=(
        "Register a custom recognizer. "
        "Use **pattern** type for regex-based detection or "
        "**deny_list** type for exact-string matching."
    ),
)
async def add_recognizer(request: RecognizerRequest) -> dict:
    if request.type == "pattern" and not request.patterns:
        raise HTTPException(
            status_code=400,
            detail="`patterns` is required for a pattern-type recognizer.",
        )
    if request.type == "deny_list" and not request.deny_list:
        raise HTTPException(
            status_code=400,
            detail="`deny_list` is required for a deny_list-type recognizer.",
        )

    registry.add_recognizer(
        name=request.name,
        supported_entity=request.supported_entity,
        supported_language=request.supported_language,
        recognizer_type=request.type,
        patterns=[p.model_dump() for p in request.patterns] if request.patterns else None,
        deny_list=request.deny_list,
        context=request.context,
    )
    return {"message": f"Recognizer '{request.name}' added successfully.", "name": request.name}


@router.delete(
    "/{name}",
    status_code=204,
    summary="Remove a custom recognizer",
    description="Remove a previously added custom recognizer by its name.",
)
async def remove_recognizer(name: str) -> None:
    if not registry.remove_recognizer(name):
        raise HTTPException(
            status_code=404,
            detail=f"Recognizer '{name}' not found.",
        )

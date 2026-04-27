from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from app.models.rule import RuleCreate, RuleResponse, RuleUpdate
from app.store import rules

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleCreate) -> RuleResponse:
    rule_id = str(uuid.uuid4())
    rule_data = payload.model_dump()
    rule_data["id"] = rule_id
    rules[rule_id] = rule_data
    return RuleResponse(**rule_data)


@router.get("", response_model=List[RuleResponse])
def list_rules() -> List[RuleResponse]:
    return [RuleResponse(**r) for r in rules.values()]


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: str) -> RuleResponse:
    rule = rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return RuleResponse(**rule)


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: str, payload: RuleUpdate) -> RuleResponse:
    rule = rules.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    update_data = payload.model_dump(exclude_none=True)
    rule.update(update_data)
    rules[rule_id] = rule
    return RuleResponse(**rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_rule(rule_id: str) -> Response:
    if rule_id not in rules:
        raise HTTPException(status_code=404, detail="Rule not found")
    del rules[rule_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)

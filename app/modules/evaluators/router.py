from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .evaluators import EvaluatorService, AssignmentCreate, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["Evaluator Assignments"])

@router.post("/")
def create_assignment(data: AssignmentCreate):
    try:
        return EvaluatorService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_assignments(
    cycle_id: Optional[str] = Query(None),
    evaluatee_id: Optional[str] = Query(None),
    evaluator_id: Optional[str] = Query(None)
):
    try:
        return EvaluatorService.list_all(cycle_id, evaluatee_id, evaluator_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{asn_id}")
def update_assignment(asn_id: str, data: AssignmentUpdate):
    try:
        return EvaluatorService.update(asn_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{asn_id}")
def remove_assignment(asn_id: str):
    try:
        return EvaluatorService.remove(asn_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
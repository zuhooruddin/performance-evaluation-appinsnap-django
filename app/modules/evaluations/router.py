from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .evaluations import EvaluationService, EvaluationCreate

router = APIRouter(prefix="/evaluations", tags=["Performance Evaluations"])

@router.post("/")
def submit_evaluation(data: EvaluationCreate):
    try:
        return EvaluationService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_evaluations(
    cycle_id: Optional[str] = Query(None),
    evaluatee_id: Optional[str] = Query(None)
):
    try:
        return EvaluationService.list_all(cycle_id, evaluatee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{eval_id}")
def get_evaluation(eval_id: str):
    try:
        return EvaluationService.get_by_id(eval_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
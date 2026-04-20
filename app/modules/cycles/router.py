from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .cycles import CycleService, CycleCreate, CycleUpdate

router = APIRouter(prefix="/cycles", tags=["Evaluation Cycles"])

@router.post("/")
def create_cycle(data: CycleCreate):
    try:
        return CycleService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_cycles(status: Optional[str] = Query(None, description="draft, active, or completed")):
    try:
        return CycleService.list_all(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{cyc_id}")
def get_cycle(cyc_id: str):
    try:
        return CycleService.get_by_id(cyc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{cyc_id}")
def update_cycle(cyc_id: str, data: CycleUpdate):
    try:
        return CycleService.update(cyc_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
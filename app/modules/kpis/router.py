from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .kpis import KPIService, KPICreate, KPIUpdate

router = APIRouter(prefix="/kpis", tags=["Team KPIs"])

@router.post("/")
def create_kpi(data: KPICreate):
    try:
        return KPIService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_kpis(
    team_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    include_archived: bool = Query(False)
):
    try:
        return KPIService.list_all(team_id, department_id, include_archived)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{kpi_id}")
def get_kpi(kpi_id: str):
    try:
        return KPIService.get_by_id(kpi_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{kpi_id}")
def update_kpi(kpi_id: str, data: KPIUpdate):
    try:
        return KPIService.update(kpi_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{kpi_id}")
def archive_kpi(kpi_id: str):
    try:
        return KPIService.archive(kpi_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
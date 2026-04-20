from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .teams import TeamService, TeamCreate, TeamUpdate

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.post("/")
def create_team(data: TeamCreate):
    try:
        return TeamService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_teams(department_id: Optional[str] = Query(None), include_archived: bool = Query(False)):
    try:
        return TeamService.list_all(department_id, include_archived)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}")
def get_team(team_id: str):
    try:
        return TeamService.get_by_id(team_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{team_id}")
def update_team(team_id: str, data: TeamUpdate):
    try:
        return TeamService.update(team_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{team_id}")
def archive_team(team_id: str):
    try:
        return TeamService.archive(team_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from .employees import EmployeeService, EmployeeCreate, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["HR Employees"])

@router.post("/")
def create_hr_profile(data: EmployeeCreate):
    try:
        return EmployeeService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_hr_profiles(
    team_id: Optional[str] = Query(None), 
    department_id: Optional[str] = Query(None),
    include_archived: bool = Query(False)
):
    try:
        return EmployeeService.list_all(team_id, department_id, include_archived)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{emp_id}")
def get_hr_profile(emp_id: str):
    try:
        return EmployeeService.get_by_id(emp_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{emp_id}")
def update_hr_profile(emp_id: str, data: EmployeeUpdate):
    try:
        return EmployeeService.update(emp_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{emp_id}")
def archive_hr_profile(emp_id: str):
    try:
        return EmployeeService.archive(emp_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
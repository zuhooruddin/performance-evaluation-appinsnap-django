from fastapi import APIRouter, HTTPException, Query
from typing import List

from .departments import DepartmentService, DepartmentCreate, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.post("/")
def create_department(data: DepartmentCreate):
    try:
        return DepartmentService.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def list_departments(include_archived: bool = Query(False)):
    try:
        return DepartmentService.list_all(include_archived)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dept_id}")
def get_department(dept_id: str):
    try:
        return DepartmentService.get_by_id(dept_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{dept_id}")
def update_department(dept_id: str, data: DepartmentUpdate):
    try:
        return DepartmentService.update(dept_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{dept_id}")
def archive_department(dept_id: str):
    try:
        return DepartmentService.archive(dept_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
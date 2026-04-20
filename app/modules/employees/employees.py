import time
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Schemas
# =========================

class EmployeeCreate(BaseModel):
    email: EmailStr = Field(..., description="Must match an existing Auth Access Profile email")
    team_id: str = Field(..., description="The ID of the team they are joining (e.g., TM-01)")

class EmployeeUpdate(BaseModel):
    team_id: Optional[str] = None
    is_active: Optional[bool] = None

# =========================
# Domain Model
# =========================

class Employee(BaseModel):
    id: str
    email: EmailStr
    team_id: str
    department_id: str  # Auto-derived from the team
    is_active: bool = True
    created_at: float
    updated_at: float

# =========================
# Service Layer
# =========================

class EmployeeService:
    COLLECTION = "employees"

    @classmethod
    def create(cls, data: EmployeeCreate) -> dict:
        # 1. Validate Auth Profile Exists (Cross-Module Integrity)
        users = Storage.load("users")
        auth_exists = any(u.get("email", "").lower() == data.email.lower() for u in users.values())
        if not auth_exists:
            raise ValueError(f"No Auth Access Profile found for '{data.email}'. Please register their access profile first.")

        # 2. Validate Team & Derive Department
        teams = Storage.load("teams")
        if data.team_id not in teams:
            raise ValueError(f"Team ID '{data.team_id}' does not exist.")
        if not teams[data.team_id].get("is_active", True):
            raise ValueError(f"Team '{teams[data.team_id]['name']}' is archived. You cannot assign employees to it.")
        
        derived_dept_id = teams[data.team_id]["department_id"]

        # 3. Check for Duplicate HR Profile
        employees = Storage.load(cls.COLLECTION)
        for emp in employees.values():
            if emp["email"].lower() == data.email.lower():
                if not emp.get("is_active", True):
                    raise ValueError(f"An HR Profile for '{data.email}' exists but is archived. Please restore it.")
                raise ValueError(f"An active HR Profile for '{data.email}' already exists.")

        emp_id = IDGenerator.generate("HR")
        now = time.time()

        new_employee = Employee(
            id=emp_id,
            email=data.email,
            team_id=data.team_id,
            department_id=derived_dept_id, # Smart auto-assignment
            is_active=True,
            created_at=now,
            updated_at=now
        ).model_dump()

        employees[emp_id] = new_employee
        Storage.save(cls.COLLECTION, employees)
        return new_employee

    @classmethod
    def list_all(cls, team_id: Optional[str] = None, department_id: Optional[str] = None, include_archived: bool = False) -> List[dict]:
        employees = Storage.load(cls.COLLECTION)
        results = []
        for emp in employees.values():
            if team_id and emp["team_id"] != team_id: continue
            if department_id and emp["department_id"] != department_id: continue
            if not include_archived and not emp.get("is_active", True): continue
            results.append(emp)
        return results

    @classmethod
    def get_by_id(cls, emp_id: str) -> dict:
        employees = Storage.load(cls.COLLECTION)
        if emp_id not in employees:
            raise ValueError("HR Profile not found.")
        return employees[emp_id]

    @classmethod
    def update(cls, emp_id: str, data: EmployeeUpdate) -> dict:
        employees = Storage.load(cls.COLLECTION)
        if emp_id not in employees:
            raise ValueError("HR Profile not found.")
        
        target = employees[emp_id]

        if data.team_id and data.team_id != target["team_id"]:
            # Validate new team and update department
            teams = Storage.load("teams")
            if data.team_id not in teams:
                raise ValueError(f"New Team ID '{data.team_id}' does not exist.")
            target["team_id"] = data.team_id
            target["department_id"] = teams[data.team_id]["department_id"]

        if data.is_active is not None:
            target["is_active"] = data.is_active

        target["updated_at"] = time.time()
        
        employees[emp_id] = target
        Storage.save(cls.COLLECTION, employees)
        return target

    @classmethod
    def archive(cls, emp_id: str) -> dict:
        employees = Storage.load(cls.COLLECTION)
        if emp_id not in employees:
            raise ValueError("HR Profile not found.")
        
        if not employees[emp_id].get("is_active", True):
            raise ValueError("HR Profile is already archived.")

        employees[emp_id]["is_active"] = False
        employees[emp_id]["updated_at"] = time.time()
        
        Storage.save(cls.COLLECTION, employees)
        return {"message": f"HR Profile '{emp_id}' archived successfully."}
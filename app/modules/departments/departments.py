import time
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator


# =========================
# Schemas (Input Validation)
# =========================

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    head_id: Optional[str] = Field(None, description="Links to Employee ID later")

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    head_id: Optional[str] = None
    is_active: Optional[bool] = None


# =========================
# Domain Model
# =========================

class Department(BaseModel):
    id: str
    name: str
    description: Optional[str]
    head_id: Optional[str]
    is_active: bool = True
    created_at: float
    updated_at: float


# =========================
# Service Layer
# =========================

class DepartmentService:
    COLLECTION = "departments"

    @classmethod
    def create(cls, data: DepartmentCreate) -> dict:
        depts = Storage.load(cls.COLLECTION)
        
        # Smart Case-Insensitive Uniqueness Check
        for dept in depts.values():
            if dept["name"].lower() == data.name.lower():
                if not dept["is_active"]:
                    raise ValueError(f"Department '{data.name}' already exists but is archived. Please restore it instead.")
                raise ValueError(f"Department '{data.name}' already exists and is active.")

        dept_id = IDGenerator.generate("DPT")
        now = time.time()

        new_dept = Department(
            id=dept_id,
            name=data.name,
            description=data.description,
            head_id=data.head_id,
            is_active=True,
            created_at=now,
            updated_at=now
        ).model_dump()

        depts[dept_id] = new_dept
        Storage.save(cls.COLLECTION, depts)
        return new_dept

    @classmethod
    def list_all(cls, include_archived: bool = False) -> List[dict]:
        depts = Storage.load(cls.COLLECTION)
        if include_archived:
            return list(depts.values())
        return [d for d in depts.values() if d["is_active"]]

    @classmethod
    def get_by_id(cls, dept_id: str) -> dict:
        depts = Storage.load(cls.COLLECTION)
        if dept_id not in depts:
            raise ValueError("Department not found.")
        return depts[dept_id]

    @classmethod
    def update(cls, dept_id: str, data: DepartmentUpdate) -> dict:
        depts = Storage.load(cls.COLLECTION)
        if dept_id not in depts:
            raise ValueError("Department not found.")
        
        target = depts[dept_id]

        # Check uniqueness if the name is being changed
        if data.name and data.name.lower() != target["name"].lower():
            if any(d["name"].lower() == data.name.lower() for d in depts.values() if d["id"] != dept_id):
                raise ValueError(f"The name '{data.name}' is already taken by another department.")
            target["name"] = data.name

        if data.description is not None:
            target["description"] = data.description
        if data.head_id is not None:
            target["head_id"] = data.head_id
        if data.is_active is not None:
            target["is_active"] = data.is_active

        target["updated_at"] = time.time()
        
        depts[dept_id] = target
        Storage.save(cls.COLLECTION, depts)
        return target

    @classmethod
    def archive(cls, dept_id: str) -> dict:
        """SaaS Best Practice: Soft Delete."""
        depts = Storage.load(cls.COLLECTION)
        if dept_id not in depts:
            raise ValueError("Department not found.")
        
        if not depts[dept_id]["is_active"]:
            raise ValueError("Department is already archived.")

        depts[dept_id]["is_active"] = False
        depts[dept_id]["updated_at"] = time.time()
        
        Storage.save(cls.COLLECTION, depts)
        return {"message": f"Department '{depts[dept_id]['name']}' archived successfully."}
import time
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator


# =========================
# Schemas (Input Validation)
# =========================

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    department_id: str = Field(..., description="Must be a valid, active Department ID")
    description: Optional[str] = None
    team_lead_id: Optional[str] = Field(None, description="Links to Employee ID later")

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    team_lead_id: Optional[str] = None
    is_active: Optional[bool] = None


# =========================
# Domain Model
# =========================

class Team(BaseModel):
    id: str
    name: str
    department_id: str
    description: Optional[str]
    team_lead_id: Optional[str]
    is_active: bool = True
    created_at: float
    updated_at: float


# =========================
# Service Layer
# =========================

class TeamService:
    COLLECTION = "teams"
    DEPTS_COLLECTION = "departments"

    @classmethod
    def _validate_department(cls, department_id: str):
        depts = Storage.load(cls.DEPTS_COLLECTION)
        if department_id not in depts:
            raise ValueError(f"Department ID '{department_id}' does not exist.")
        if not depts[department_id].get("is_active", True):
            raise ValueError(f"Department '{depts[department_id]['name']}' is archived. You cannot add teams to it.")
        return depts[department_id]

    @classmethod
    def create(cls, data: TeamCreate) -> dict:
        # 1. Ensure the parent department is valid and active
        cls._validate_department(data.department_id)

        teams = Storage.load(cls.COLLECTION)
        
        # 2. Composite Uniqueness Check (Name must be unique WITHIN the Department)
        for team in teams.values():
            if team["department_id"] == data.department_id and team["name"].lower() == data.name.lower():
                if not team.get("is_active", True):
                    raise ValueError(f"Team '{data.name}' already exists in this department but is archived.")
                raise ValueError(f"Team '{data.name}' already exists in this department.")

        team_id = IDGenerator.generate("TM")
        now = time.time()

        new_team = Team(
            id=team_id,
            name=data.name,
            department_id=data.department_id,
            description=data.description,
            team_lead_id=data.team_lead_id,
            is_active=True,
            created_at=now,
            updated_at=now
        ).model_dump()

        teams[team_id] = new_team
        Storage.save(cls.COLLECTION, teams)
        return new_team

    @classmethod
    def list_all(cls, department_id: Optional[str] = None, include_archived: bool = False) -> List[dict]:
        teams = Storage.load(cls.COLLECTION)
        results = []
        for t in teams.values():
            # Filter by department if provided
            if department_id and t["department_id"] != department_id:
                continue
            # Filter by active status
            if not include_archived and not t.get("is_active", True):
                continue
            results.append(t)
        return results

    @classmethod
    def get_by_id(cls, team_id: str) -> dict:
        teams = Storage.load(cls.COLLECTION)
        if team_id not in teams:
            raise ValueError("Team not found.")
        return teams[team_id]

    @classmethod
    def update(cls, team_id: str, data: TeamUpdate) -> dict:
        teams = Storage.load(cls.COLLECTION)
        if team_id not in teams:
            raise ValueError("Team not found.")
        
        target = teams[team_id]

        # Check uniqueness if the name is being changed
        if data.name and data.name.lower() != target["name"].lower():
            conflict = any(
                t["name"].lower() == data.name.lower() and 
                t["department_id"] == target["department_id"] 
                for tid, t in teams.items() if tid != team_id
            )
            if conflict:
                raise ValueError(f"The name '{data.name}' is already taken in this department.")
            target["name"] = data.name

        if data.description is not None:
            target["description"] = data.description
        if data.team_lead_id is not None:
            target["team_lead_id"] = data.team_lead_id
        if data.is_active is not None:
            target["is_active"] = data.is_active

        target["updated_at"] = time.time()
        
        teams[team_id] = target
        Storage.save(cls.COLLECTION, teams)
        return target

    @classmethod
    def archive(cls, team_id: str) -> dict:
        teams = Storage.load(cls.COLLECTION)
        if team_id not in teams:
            raise ValueError("Team not found.")
        
        if not teams[team_id].get("is_active", True):
            raise ValueError("Team is already archived.")

        teams[team_id]["is_active"] = False
        teams[team_id]["updated_at"] = time.time()
        
        Storage.save(cls.COLLECTION, teams)
        return {"message": f"Team '{teams[team_id]['name']}' archived successfully."}
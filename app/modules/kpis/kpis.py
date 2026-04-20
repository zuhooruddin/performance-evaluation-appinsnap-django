import time
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Schemas
# =========================

class KPICreate(BaseModel):
    team_id: str = Field(..., description="The ID of the Team this KPI applies to (e.g., TM-01)")
    title: str = Field(..., min_length=3, max_length=150, description="e.g., Code Quality, Bug Resolve Rate")
    description: str = Field(..., description="Detailed explanation of how this KPI is measured")
    weight: float = Field(..., gt=0, le=1.0, description="Percentage weight of this KPI (e.g., 0.5 for 50%)")

class KPIUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0, le=1.0)
    is_active: Optional[bool] = None

# =========================
# Domain Model
# =========================

class KPI(BaseModel):
    id: str
    team_id: str
    department_id: str  # Auto-derived for easier querying later
    title: str
    description: str
    weight: float
    is_active: bool = True
    created_at: float
    updated_at: float

# =========================
# Service Layer
# =========================

class KPIService:
    COLLECTION = "kpis"

    @classmethod
    def create(cls, data: KPICreate) -> dict:
        # 1. Validate Target Team
        teams = Storage.load("teams")
        if data.team_id not in teams:
            raise ValueError(f"Team ID '{data.team_id}' does not exist.")
        if not teams[data.team_id].get("is_active", True):
            raise ValueError(f"Team '{teams[data.team_id]['name']}' is archived. You cannot add KPIs to it.")
            
        department_id = teams[data.team_id]["department_id"]

        # 2. Composite Uniqueness Check (Title must be unique within the Team)
        kpis = Storage.load(cls.COLLECTION)
        for k in kpis.values():
            if k["team_id"] == data.team_id and k["title"].lower() == data.title.lower():
                if not k.get("is_active", True):
                    raise ValueError(f"KPI '{data.title}' exists in this team but is archived. Please restore it.")
                raise ValueError(f"KPI '{data.title}' already exists for this team.")

        # 3. Optional strictness: Warn if total team weight > 1.0 
        # (We will allow it to save, but a frontend could use this to show a warning)
        current_team_weight = sum(k["weight"] for k in kpis.values() if k["team_id"] == data.team_id and k.get("is_active", True))
        if current_team_weight + data.weight > 1.0:
            print(f"⚠️ Warning: Total KPI weight for Team '{data.team_id}' now exceeds 100% (1.0).")

        kpi_id = IDGenerator.generate("KPI")
        now = time.time()

        new_kpi = KPI(
            id=kpi_id,
            team_id=data.team_id,
            department_id=department_id,
            title=data.title,
            description=data.description,
            weight=data.weight,
            is_active=True,
            created_at=now,
            updated_at=now
        ).model_dump()

        kpis[kpi_id] = new_kpi
        Storage.save(cls.COLLECTION, kpis)
        return new_kpi

    @classmethod
    def list_all(cls, team_id: Optional[str] = None, department_id: Optional[str] = None, include_archived: bool = False) -> List[dict]:
        kpis = Storage.load(cls.COLLECTION)
        results = []
        for k in kpis.values():
            if not include_archived and not k.get("is_active", True): continue
            if team_id and k["team_id"] != team_id: continue
            if department_id and k["department_id"] != department_id: continue
            results.append(k)
        return results

    @classmethod
    def get_by_id(cls, kpi_id: str) -> dict:
        kpis = Storage.load(cls.COLLECTION)
        if kpi_id not in kpis:
            raise ValueError("KPI not found.")
        return kpis[kpi_id]

    @classmethod
    def update(cls, kpi_id: str, data: KPIUpdate) -> dict:
        kpis = Storage.load(cls.COLLECTION)
        if kpi_id not in kpis:
            raise ValueError("KPI not found.")
        
        target = kpis[kpi_id]

        if data.title and data.title.lower() != target["title"].lower():
            # Uniqueness check for new title within the same team
            conflict = any(
                k["title"].lower() == data.title.lower() and k["team_id"] == target["team_id"]
                for kid, k in kpis.items() if kid != kpi_id
            )
            if conflict:
                raise ValueError(f"KPI title '{data.title}' is already used in this team.")
            target["title"] = data.title

        if data.description is not None:
            target["description"] = data.description
        if data.weight is not None:
            target["weight"] = data.weight
        if data.is_active is not None:
            target["is_active"] = data.is_active

        target["updated_at"] = time.time()
        kpis[kpi_id] = target
        Storage.save(cls.COLLECTION, kpis)
        return target

    @classmethod
    def archive(cls, kpi_id: str) -> dict:
        kpis = Storage.load(cls.COLLECTION)
        if kpi_id not in kpis:
            raise ValueError("KPI not found.")
        
        if not kpis[kpi_id].get("is_active", True):
            raise ValueError("KPI is already archived.")

        kpis[kpi_id]["is_active"] = False
        kpis[kpi_id]["updated_at"] = time.time()
        
        Storage.save(cls.COLLECTION, kpis)
        return {"message": f"KPI '{kpis[kpi_id]['title']}' archived successfully."}
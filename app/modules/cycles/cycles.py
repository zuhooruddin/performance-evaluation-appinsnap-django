import time
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Enums & Schemas
# =========================

class CycleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"

class CycleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="e.g., Q1 2026 Evaluation")
    start_date: str = Field(..., description="Format: YYYY-MM-DD")
    end_date: str = Field(..., description="Format: YYYY-MM-DD")
    description: Optional[str] = None

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    @model_validator(mode='after')
    def check_dates(self):
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        if end <= start:
            raise ValueError("End date must be strictly after the start date.")
        return self

class CycleUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CycleStatus] = None

# =========================
# Domain Model
# =========================

class Cycle(BaseModel):
    id: str
    name: str
    start_date: str
    end_date: str
    description: Optional[str]
    status: str = CycleStatus.DRAFT.value
    created_at: float
    updated_at: float

# =========================
# Service Layer
# =========================

class CycleService:
    COLLECTION = "cycles"

    @classmethod
    def create(cls, data: CycleCreate) -> dict:
        cycles = Storage.load(cls.COLLECTION)
        
        # Uniqueness Check
        if any(c["name"].lower() == data.name.lower() for c in cycles.values()):
            raise ValueError(f"An Evaluation Cycle named '{data.name}' already exists.")

        cyc_id = IDGenerator.generate("CYC")
        now = time.time()

        new_cycle = Cycle(
            id=cyc_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            description=data.description,
            status=CycleStatus.DRAFT.value,
            created_at=now,
            updated_at=now
        ).model_dump(mode='json')

        cycles[cyc_id] = new_cycle
        Storage.save(cls.COLLECTION, cycles)
        return new_cycle

    @classmethod
    def list_all(cls, status: Optional[str] = None) -> List[dict]:
        cycles = Storage.load(cls.COLLECTION)
        if status:
            return [c for c in cycles.values() if c["status"] == status.lower()]
        return list(cycles.values())

    @classmethod
    def get_by_id(cls, cyc_id: str) -> dict:
        cycles = Storage.load(cls.COLLECTION)
        if cyc_id not in cycles:
            raise ValueError("Cycle not found.")
        return cycles[cyc_id]

    @classmethod
    def update(cls, cyc_id: str, data: CycleUpdate) -> dict:
        cycles = Storage.load(cls.COLLECTION)
        if cyc_id not in cycles:
            raise ValueError("Cycle not found.")
        
        target = cycles[cyc_id]

        # Name Uniqueness Check
        if data.name and data.name.lower() != target["name"].lower():
            if any(c["name"].lower() == data.name.lower() for cid, c in cycles.items() if cid != cyc_id):
                raise ValueError("Cycle name already exists.")
            target["name"] = data.name

        # Date Validation if dates are being updated
        new_start = data.start_date or target["start_date"]
        new_end = data.end_date or target["end_date"]
        if datetime.strptime(new_end, "%Y-%m-%d") <= datetime.strptime(new_start, "%Y-%m-%d"):
            raise ValueError("End date must be after the start date.")
        
        target["start_date"] = new_start
        target["end_date"] = new_end
        
        if data.description is not None:
            target["description"] = data.description

        # State Machine Logic
        if data.status and data.status.value != target["status"]:
            if data.status == CycleStatus.ACTIVE:
                # Ensure no other cycle is currently ACTIVE
                if any(c["status"] == CycleStatus.ACTIVE.value for cid, c in cycles.items() if cid != cyc_id):
                    raise ValueError("Another Evaluation Cycle is currently ACTIVE. Please complete it before activating a new one.")
            
            # Cannot reopen a completed cycle (SaaS Data Integrity rule)
            if target["status"] == CycleStatus.COMPLETED.value:
                raise ValueError("Cannot modify the status of a COMPLETED cycle.")

            target["status"] = data.status.value

        target["updated_at"] = time.time()
        cycles[cyc_id] = target
        Storage.save(cls.COLLECTION, cycles)
        return target
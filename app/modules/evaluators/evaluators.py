import time
from typing import List, Optional
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Schemas
# =========================

class AssignmentCreate(BaseModel):
    cycle_id: str = Field(..., description="The Evaluation Cycle ID (e.g., CYC-01)")
    evaluatee_id: str = Field(..., description="The HR Profile ID of the person being evaluated")
    evaluator_id: str = Field(..., description="The HR Profile ID of the person doing the grading")
    evaluator_role: str = Field(..., description="e.g., Line Manager, HR, Peer, CTO")
    weight: float = Field(..., gt=0, description="Max points this evaluator can give (e.g., 20.0 or 5.0)")

class AssignmentUpdate(BaseModel):
    evaluator_role: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

# =========================
# Domain Model
# =========================

class Assignment(BaseModel):
    id: str
    cycle_id: str
    evaluatee_id: str
    evaluator_id: str
    evaluator_role: str
    weight: float
    is_active: bool = True
    created_at: float
    updated_at: float

# =========================
# Service Layer
# =========================

class EvaluatorService:
    COLLECTION = "assignments"

    @classmethod
    def _validate_integrity(cls, data: AssignmentCreate):
        # 1. Validate Cycle
        cycles = Storage.load("cycles")
        if data.cycle_id not in cycles:
            raise ValueError(f"Cycle '{data.cycle_id}' does not exist.")
        if cycles[data.cycle_id]["status"] == "completed":
            raise ValueError(f"Cycle '{data.cycle_id}' is COMPLETED. You cannot assign evaluators to a closed cycle.")

        # 2. Validate HR Profiles (Employees)
        employees = Storage.load("employees")
        if data.evaluatee_id not in employees:
            raise ValueError(f"Evaluatee '{data.evaluatee_id}' does not exist.")
        if not employees[data.evaluatee_id].get("is_active", True):
            raise ValueError(f"Evaluatee '{data.evaluatee_id}' is archived/inactive.")

        if data.evaluator_id not in employees:
            raise ValueError(f"Evaluator '{data.evaluator_id}' does not exist.")
        if not employees[data.evaluator_id].get("is_active", True):
            raise ValueError(f"Evaluator '{data.evaluator_id}' is archived/inactive.")

        # 3. Prevent Self-Evaluation Check
        if data.evaluatee_id == data.evaluator_id:
            raise ValueError("An employee cannot be assigned to evaluate themselves.")

    @classmethod
    def create(cls, data: AssignmentCreate) -> dict:
        cls._validate_integrity(data)

        assignments = Storage.load(cls.COLLECTION)
        
        # 4. Prevent Duplicate Assignments
        for asn in assignments.values():
            if (asn["cycle_id"] == data.cycle_id and 
                asn["evaluatee_id"] == data.evaluatee_id and 
                asn["evaluator_id"] == data.evaluator_id and
                asn.get("is_active", True)):
                raise ValueError("This evaluator is already assigned to this evaluatee for this cycle.")

        asn_id = IDGenerator.generate("ASN")
        now = time.time()

        new_assignment = Assignment(
            id=asn_id,
            cycle_id=data.cycle_id,
            evaluatee_id=data.evaluatee_id,
            evaluator_id=data.evaluator_id,
            evaluator_role=data.evaluator_role,
            weight=data.weight,
            is_active=True,
            created_at=now,
            updated_at=now
        ).model_dump()

        assignments[asn_id] = new_assignment
        Storage.save(cls.COLLECTION, assignments)
        return new_assignment

    @classmethod
    def list_all(cls, cycle_id: Optional[str] = None, evaluatee_id: Optional[str] = None, evaluator_id: Optional[str] = None) -> List[dict]:
        assignments = Storage.load(cls.COLLECTION)
        results = []
        for asn in assignments.values():
            if not asn.get("is_active", True): continue
            if cycle_id and asn["cycle_id"] != cycle_id: continue
            if evaluatee_id and asn["evaluatee_id"] != evaluatee_id: continue
            if evaluator_id and asn["evaluator_id"] != evaluator_id: continue
            results.append(asn)
        return results

    @classmethod
    def update(cls, asn_id: str, data: AssignmentUpdate) -> dict:
        assignments = Storage.load(cls.COLLECTION)
        if asn_id not in assignments:
            raise ValueError("Assignment not found.")
        
        target = assignments[asn_id]

        # Ensure we don't modify assignments in a completed cycle
        cycles = Storage.load("cycles")
        if cycles.get(target["cycle_id"], {}).get("status") == "completed":
             raise ValueError("Cannot update assignments in a COMPLETED cycle.")

        if data.evaluator_role is not None:
            target["evaluator_role"] = data.evaluator_role
        if data.weight is not None:
            target["weight"] = data.weight
        if data.is_active is not None:
            target["is_active"] = data.is_active

        target["updated_at"] = time.time()
        
        assignments[asn_id] = target
        Storage.save(cls.COLLECTION, assignments)
        return target

    @classmethod
    def remove(cls, asn_id: str) -> dict:
        """Soft delete for assignments."""
        assignments = Storage.load(cls.COLLECTION)
        if asn_id not in assignments:
            raise ValueError("Assignment not found.")
        
        cycles = Storage.load("cycles")
        if cycles.get(assignments[asn_id]["cycle_id"], {}).get("status") == "completed":
             raise ValueError("Cannot remove assignments from a COMPLETED cycle.")

        assignments[asn_id]["is_active"] = False
        assignments[asn_id]["updated_at"] = time.time()
        
        Storage.save(cls.COLLECTION, assignments)
        return {"message": f"Assignment '{asn_id}' removed successfully."}
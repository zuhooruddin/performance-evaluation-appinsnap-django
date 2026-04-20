import time
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Schemas
# =========================

class KPIScoreInput(BaseModel):
    kpi_id: str
    score: float = Field(..., ge=0, le=100, description="Score from 0 to 100")

class EvaluationCreate(BaseModel):
    assignment_id: str = Field(..., description="The ASN-xx ID linking the Evaluator and Evaluatee")
    kpi_scores: List[KPIScoreInput] = Field(..., min_length=1)
    comments: Optional[str] = Field(None, description="Qualitative feedback")

# =========================
# Domain Model
# =========================

class Evaluation(BaseModel):
    id: str
    assignment_id: str
    cycle_id: str
    evaluatee_id: str
    evaluator_id: str
    kpi_scores: List[dict]
    total_points_earned: float
    max_points_possible: float
    comments: Optional[str]
    created_at: float

# =========================
# Service Layer
# =========================

class EvaluationService:
    COLLECTION = "evaluations"

    @classmethod
    def create(cls, data: EvaluationCreate) -> dict:
        assignments = Storage.load("assignments")
        if data.assignment_id not in assignments:
            raise ValueError("Assignment not found.")
        
        asn = assignments[data.assignment_id]
        if not asn.get("is_active", True):
            raise ValueError("This assignment is no longer active.")

        # 1. Validate Cycle is Active
        cycles = Storage.load("cycles")
        cycle_id = asn["cycle_id"]
        if cycles.get(cycle_id, {}).get("status") != "active":
            raise ValueError("Evaluations can only be submitted for an ACTIVE cycle.")

        # 2. Prevent Duplicate Submission
        evals = Storage.load(cls.COLLECTION)
        if any(e["assignment_id"] == data.assignment_id for e in evals.values()):
            raise ValueError("An evaluation has already been submitted for this assignment.")

        # 3. Load Evaluatee's Team to get KPIs
        employees = Storage.load("employees")
        evaluatee = employees[asn["evaluatee_id"]]
        team_id = evaluatee["team_id"]

        all_kpis = Storage.load("kpis")
        team_kpis = {k_id: k for k_id, k in all_kpis.items() if k["team_id"] == team_id and k.get("is_active", True)}

        if not team_kpis:
            raise ValueError(f"No active KPIs found for the evaluatee's team ({team_id}). Admin must configure KPIs first.")

        # 4. Math Engine: Calculate Final Points
        submitted_scores = {s.kpi_id: s.score for s in data.kpi_scores}
        total_kpi_weight = sum(k["weight"] for k in team_kpis.values())
        
        points_earned = 0.0
        processed_scores = []

        for k_id, kpi in team_kpis.items():
            if k_id not in submitted_scores:
                raise ValueError(f"Missing score for KPI: {kpi['title']} ({k_id})")
            
            raw_score = submitted_scores[k_id]
            # Formula: (Score / 100) * (Normalized KPI Weight) * Assignment Max Points
            normalized_weight = kpi["weight"] / total_kpi_weight
            points = (raw_score / 100) * normalized_weight * asn["weight"]
            points_earned += points

            processed_scores.append({
                "kpi_id": k_id,
                "kpi_title": kpi["title"],
                "raw_score": raw_score,
                "points_earned": round(points, 2)
            })

        eval_id = IDGenerator.generate("EVL")
        new_evaluation = Evaluation(
            id=eval_id,
            assignment_id=asn["id"],
            cycle_id=cycle_id,
            evaluatee_id=asn["evaluatee_id"],
            evaluator_id=asn["evaluator_id"],
            kpi_scores=processed_scores,
            total_points_earned=round(points_earned, 2),
            max_points_possible=asn["weight"],
            comments=data.comments,
            created_at=time.time()
        ).model_dump()

        evals[eval_id] = new_evaluation
        Storage.save(cls.COLLECTION, evals)
        return new_evaluation

    @classmethod
    def list_all(cls, cycle_id: Optional[str] = None, evaluatee_id: Optional[str] = None) -> List[dict]:
        evals = Storage.load(cls.COLLECTION)
        results = []
        for e in evals.values():
            if cycle_id and e["cycle_id"] != cycle_id: continue
            if evaluatee_id and e["evaluatee_id"] != evaluatee_id: continue
            results.append(e)
        return results

    @classmethod
    def get_by_id(cls, eval_id: str) -> dict:
        evals = Storage.load(cls.COLLECTION)
        if eval_id not in evals:
            raise ValueError("Evaluation not found.")
        return evals[eval_id]
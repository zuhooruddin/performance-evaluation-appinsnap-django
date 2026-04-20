import time
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.storage import Storage
from app.core.rbac import get_session, require_any_permission


Role = str
Quarter = Literal["Q1", "Q2", "Q3", "Q4"]
EvaluationStatus = Literal["draft", "submitted", "hr_scored", "finalized"]


class RoleDefinition(BaseModel):
    id: Role
    label: str
    permissions: List[str] = Field(default_factory=list)
    participatesInEvaluation: bool = False
    maxPointsPerQuarter: int = 0


class Team(BaseModel):
    id: str
    name: str
    department: str
    managerId: str


class Employee(BaseModel):
    id: str
    name: str
    email: str
    teamId: str
    role: Role


class KPI(BaseModel):
    id: str
    teamId: str
    title: str
    description: Optional[str] = None
    weight: float = Field(ge=0.0, le=1.0)


class KPIScore(BaseModel):
    kpiId: str
    score: float
    comment: Optional[str] = None


class HRScore(BaseModel):
    category: str
    score: float
    comment: Optional[str] = None


class Evaluation(BaseModel):
    id: str
    employeeId: str
    quarter: Quarter
    year: int
    managerScores: List[KPIScore] = Field(default_factory=list)
    managerComment: Optional[str] = None
    managerImprovementAreas: Optional[str] = None
    managerScore: float = 0
    hrScores: List[HRScore] = Field(default_factory=list)
    hrScore: float = 0
    totalScore: float = 0
    status: EvaluationStatus = "draft"
    updatedAt: str


class UpsertRoleRequest(BaseModel):
    id: Optional[str] = None
    label: str
    permissions: List[str] = Field(default_factory=list)
    participatesInEvaluation: bool = False
    maxPointsPerQuarter: int = 0


class CreateTeamRequest(BaseModel):
    name: str = Field(min_length=2)
    department: str = Field(min_length=2)
    managerId: str


class UpdateTeamRequest(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    managerId: Optional[str] = None


class CreateEmployeeRequest(BaseModel):
    name: str = Field(min_length=2)
    email: str = Field(min_length=3)
    teamId: str
    role: Role


class UpdateEmployeeRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    teamId: Optional[str] = None
    role: Optional[Role] = None


class CreateKPIRequest(BaseModel):
    teamId: str
    title: str = Field(min_length=2)
    description: Optional[str] = None
    weight: float = Field(ge=0.0, le=1.0)


class UpdateKPIRequest(BaseModel):
    teamId: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SaveManagerDraftRequest(BaseModel):
    employeeId: str
    quarter: Quarter
    year: int
    managerScores: List[KPIScore] = Field(default_factory=list)
    managerComment: Optional[str] = None
    managerImprovementAreas: Optional[str] = None


class SubmitManagerRequest(BaseModel):
    evaluationId: str


class AssignHRScoreRequest(BaseModel):
    evaluationId: str
    hrScores: List[HRScore] = Field(default_factory=list)


class FinalizeRequest(BaseModel):
    evaluationId: str


router = APIRouter(prefix="/pet", tags=["PET (Frontend Compatible)"])


def _iso_now() -> str:
    # Avoid extra deps; client only needs an ISO-ish string
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_map(collection: str) -> Dict[str, Any]:
    data = Storage.load(collection)
    return data if isinstance(data, dict) else {}


def _save_map(collection: str, data: Dict[str, Any]) -> None:
    Storage.save(collection, data)


def _ensure_seeded() -> None:
    # Seed roles only. Org data (teams/employees/kpis/evaluations) must come from real storage.
    roles = _load_map("pet_roles")
    if not roles:
        seed_roles = [
            RoleDefinition(
                id="admin",
                label="Admin",
                permissions=[
                    "roles:manage",
                    "kpis:manage",
                    "teams:manage",
                    "employees:manage",
                    "evaluation:view_all",
                    "reports:view",
                    "settings:view",
                ],
                participatesInEvaluation=False,
                maxPointsPerQuarter=0,
            ),
            RoleDefinition(
                id="manager",
                label="Line Manager",
                permissions=["evaluation:manager_score", "kpis:manage", "settings:view"],
                participatesInEvaluation=True,
                maxPointsPerQuarter=20,
            ),
            RoleDefinition(
                id="hr",
                label="HR",
                permissions=["evaluation:hr_score", "reports:view", "settings:view"],
                participatesInEvaluation=True,
                maxPointsPerQuarter=5,
            ),
            RoleDefinition(
                id="employee",
                label="Employee",
                permissions=["settings:view"],
                participatesInEvaluation=False,
                maxPointsPerQuarter=0,
            ),
        ]
        _save_map("pet_roles", {r.id: r.model_dump() for r in seed_roles})
    return


@router.get("/seed")
def seed():
    _ensure_seeded()
    return {"message": "seeded"}


@router.get("/roles")
def list_roles(_: dict = Depends(get_session)) -> List[RoleDefinition]:
    _ensure_seeded()
    data = _load_map("pet_roles")
    return [RoleDefinition(**v) for v in data.values()]


@router.put("/roles/{role_id}")
def upsert_role(
    role_id: str,
    payload: UpsertRoleRequest,
    _: dict = Depends(require_any_permission("roles:manage")),
) -> RoleDefinition:
    _ensure_seeded()
    data = _load_map("pet_roles")
    rid = (payload.id or role_id or "").strip() or role_id
    role = RoleDefinition(
        id=rid,
        label=payload.label.strip() or rid,
        permissions=payload.permissions,
        participatesInEvaluation=bool(payload.participatesInEvaluation),
        maxPointsPerQuarter=int(payload.maxPointsPerQuarter),
    )
    data[role.id] = role.model_dump()
    _save_map("pet_roles", data)
    return role


@router.delete("/roles/{role_id}")
def delete_role(role_id: str, _: dict = Depends(require_any_permission("roles:manage"))):
    _ensure_seeded()
    if role_id in {"admin", "manager", "hr", "employee"}:
        raise HTTPException(status_code=400, detail="Core roles cannot be deleted.")
    data = _load_map("pet_roles")
    if role_id in data:
        del data[role_id]
        _save_map("pet_roles", data)
    return {"message": "deleted"}


@router.get("/teams")
def list_teams(_: dict = Depends(get_session)) -> List[Team]:
    _ensure_seeded()
    data = _load_map("pet_teams")
    return [Team(**v) for v in data.values()]


@router.post("/teams")
def create_team(payload: CreateTeamRequest, _: dict = Depends(require_any_permission("teams:manage"))) -> Team:
    _ensure_seeded()
    data = _load_map("pet_teams")
    team_id = f"t_{int(time.time() * 1000)}"
    team = Team(id=team_id, name=payload.name, department=payload.department, managerId=payload.managerId)
    data[team.id] = team.model_dump()
    _save_map("pet_teams", data)
    return team


@router.patch("/teams/{team_id}")
def update_team(
    team_id: str,
    payload: UpdateTeamRequest,
    _: dict = Depends(require_any_permission("teams:manage")),
) -> Team:
    _ensure_seeded()
    data = _load_map("pet_teams")
    if team_id not in data:
        raise HTTPException(status_code=404, detail="Team not found")
    current = Team(**data[team_id])
    next_team = current.model_copy(
        update={
            "name": payload.name if payload.name is not None else current.name,
            "department": payload.department if payload.department is not None else current.department,
            "managerId": payload.managerId if payload.managerId is not None else current.managerId,
        }
    )
    data[team_id] = next_team.model_dump()
    _save_map("pet_teams", data)
    return next_team


@router.delete("/teams/{team_id}")
def delete_team(team_id: str, _: dict = Depends(require_any_permission("teams:manage"))):
    _ensure_seeded()
    data = _load_map("pet_teams")
    if team_id in data:
        del data[team_id]
        _save_map("pet_teams", data)
    return {"message": "deleted"}


@router.get("/employees")
def list_employees(_: dict = Depends(get_session)) -> List[Employee]:
    _ensure_seeded()
    data = _load_map("pet_employees")
    return [Employee(**v) for v in data.values()]


@router.post("/employees")
def create_employee(
    payload: CreateEmployeeRequest,
    _: dict = Depends(require_any_permission("employees:manage")),
) -> Employee:
    _ensure_seeded()
    data = _load_map("pet_employees")
    emp_id = f"u_{int(time.time() * 1000)}"
    employee = Employee(
        id=emp_id,
        name=payload.name,
        email=payload.email,
        teamId=payload.teamId,
        role=payload.role,
    )
    data[employee.id] = employee.model_dump()
    _save_map("pet_employees", data)
    return employee


@router.patch("/employees/{employee_id}")
def update_employee(
    employee_id: str,
    payload: UpdateEmployeeRequest,
    _: dict = Depends(require_any_permission("employees:manage")),
) -> Employee:
    _ensure_seeded()
    data = _load_map("pet_employees")
    if employee_id not in data:
        raise HTTPException(status_code=404, detail="Employee not found")
    current = Employee(**data[employee_id])
    next_emp = current.model_copy(
        update={
            "name": payload.name if payload.name is not None else current.name,
            "email": payload.email if payload.email is not None else current.email,
            "teamId": payload.teamId if payload.teamId is not None else current.teamId,
            "role": payload.role if payload.role is not None else current.role,
        }
    )
    data[employee_id] = next_emp.model_dump()
    _save_map("pet_employees", data)
    return next_emp


@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: str, _: dict = Depends(require_any_permission("employees:manage"))):
    _ensure_seeded()
    data = _load_map("pet_employees")
    if employee_id in data:
        del data[employee_id]
        _save_map("pet_employees", data)
    return {"message": "deleted"}


@router.get("/kpis")
def list_kpis(_: dict = Depends(get_session)) -> List[KPI]:
    _ensure_seeded()
    data = _load_map("pet_kpis")
    return [KPI(**v) for v in data.values()]


@router.post("/kpis")
def create_kpi(payload: CreateKPIRequest, _: dict = Depends(require_any_permission("kpis:manage"))) -> KPI:
    _ensure_seeded()
    data = _load_map("pet_kpis")
    kpi_id = f"kpi_{int(time.time() * 1000)}"
    kpi = KPI(id=kpi_id, teamId=payload.teamId, title=payload.title, description=payload.description, weight=payload.weight)
    data[kpi.id] = kpi.model_dump()
    _save_map("pet_kpis", data)
    return kpi


@router.patch("/kpis/{kpi_id}")
def update_kpi(
    kpi_id: str,
    payload: UpdateKPIRequest,
    _: dict = Depends(require_any_permission("kpis:manage")),
) -> KPI:
    _ensure_seeded()
    data = _load_map("pet_kpis")
    if kpi_id not in data:
        raise HTTPException(status_code=404, detail="KPI not found")
    current = KPI(**data[kpi_id])
    next_kpi = current.model_copy(
        update={
            "teamId": payload.teamId if payload.teamId is not None else current.teamId,
            "title": payload.title if payload.title is not None else current.title,
            "description": payload.description if payload.description is not None else current.description,
            "weight": payload.weight if payload.weight is not None else current.weight,
        }
    )
    data[kpi_id] = next_kpi.model_dump()
    _save_map("pet_kpis", data)
    return next_kpi


@router.delete("/kpis/{kpi_id}")
def delete_kpi(kpi_id: str, _: dict = Depends(require_any_permission("kpis:manage"))):
    _ensure_seeded()
    data = _load_map("pet_kpis")
    if kpi_id in data:
        del data[kpi_id]
        _save_map("pet_kpis", data)
    return {"message": "deleted"}


@router.get("/evaluations")
def list_evaluations(_: dict = Depends(get_session)) -> List[Evaluation]:
    _ensure_seeded()
    data = _load_map("pet_evaluations")
    return [Evaluation(**v) for v in data.values()]


@router.post("/evaluations/manager-draft")
def save_manager_draft(
    payload: SaveManagerDraftRequest,
    _: dict = Depends(require_any_permission("evaluation:manager_score")),
) -> Evaluation:
    _ensure_seeded()
    data = _load_map("pet_evaluations")
    eid = f"e_{payload.year}_{payload.employeeId}_{payload.quarter.lower()}_{int(time.time() * 1000)}"
    manager_score = float(sum([s.score for s in payload.managerScores]))
    hr_score = 0.0
    total = manager_score + hr_score
    ev = Evaluation(
        id=eid,
        employeeId=payload.employeeId,
        quarter=payload.quarter,
        year=payload.year,
        managerScores=payload.managerScores,
        managerComment=payload.managerComment,
        managerImprovementAreas=payload.managerImprovementAreas,
        managerScore=manager_score,
        hrScores=[],
        hrScore=hr_score,
        totalScore=total,
        status="draft",
        updatedAt=_iso_now(),
    )
    data[ev.id] = ev.model_dump()
    _save_map("pet_evaluations", data)
    return ev


@router.post("/evaluations/submit-manager")
def submit_manager(
    payload: SubmitManagerRequest,
    _: dict = Depends(require_any_permission("evaluation:manager_score")),
) -> Evaluation:
    _ensure_seeded()
    data = _load_map("pet_evaluations")
    if payload.evaluationId not in data:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    current = Evaluation(**data[payload.evaluationId])
    next_ev = current.model_copy(update={"status": "submitted", "updatedAt": _iso_now()})
    data[next_ev.id] = next_ev.model_dump()
    _save_map("pet_evaluations", data)
    return next_ev


@router.post("/evaluations/assign-hr")
def assign_hr(
    payload: AssignHRScoreRequest,
    _: dict = Depends(require_any_permission("evaluation:hr_score")),
) -> Evaluation:
    _ensure_seeded()
    data = _load_map("pet_evaluations")
    if payload.evaluationId not in data:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    current = Evaluation(**data[payload.evaluationId])
    hr_score = float(sum([s.score for s in payload.hrScores]))
    total = float(current.managerScore) + hr_score
    next_ev = current.model_copy(
        update={
            "hrScores": payload.hrScores,
            "hrScore": hr_score,
            "totalScore": total,
            "status": "hr_scored",
            "updatedAt": _iso_now(),
        }
    )
    data[next_ev.id] = next_ev.model_dump()
    _save_map("pet_evaluations", data)
    return next_ev


@router.post("/evaluations/finalize")
def finalize(payload: FinalizeRequest, _: dict = Depends(require_any_permission("evaluation:hr_score"))) -> Evaluation:
    _ensure_seeded()
    data = _load_map("pet_evaluations")
    if payload.evaluationId not in data:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    current = Evaluation(**data[payload.evaluationId])
    if current.status != "hr_scored":
        raise HTTPException(status_code=400, detail="Only HR-scored evaluations can be finalized")
    next_ev = current.model_copy(update={"status": "finalized", "updatedAt": _iso_now()})
    data[next_ev.id] = next_ev.model_dump()
    _save_map("pet_evaluations", data)
    return next_ev


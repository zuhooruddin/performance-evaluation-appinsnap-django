from __future__ import annotations

from typing import Callable, Dict, Optional, Set

from fastapi import Depends, HTTPException, Request

from app.core.storage import Storage


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "roles:manage",
        "kpis:manage",
        "teams:manage",
        "employees:manage",
        "evaluation:view_all",
        "reports:view",
        "settings:view",
        "evaluation:manager_score",
        "evaluation:hr_score",
    },
    "manager": {"evaluation:manager_score", "kpis:manage", "settings:view"},
    "hr": {"evaluation:hr_score", "reports:view", "settings:view"},
    "employee": {"settings:view"},
}


def _extract_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) != 2:
        return None
    scheme, token = parts[0].strip().lower(), parts[1].strip()
    if scheme != "bearer" or not token:
        return None
    return token


def get_session(request: Request) -> dict:
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token")
    sessions = Storage.load("sessions")
    if token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")
    return sessions[token]


def require_any_permission(*perms: str):
    required = set(perms)

    def _dep(session: dict = Depends(get_session)) -> dict:
        role = str(session.get("role", "")).lower()
        allowed = ROLE_PERMISSIONS.get(role, set())
        if not required.intersection(allowed) and "ALL" not in set(session.get("permissions", [])):
            raise HTTPException(status_code=403, detail="Forbidden for this role")
        return session

    return _dep


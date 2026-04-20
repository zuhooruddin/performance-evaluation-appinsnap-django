import os
import sys
from typing import Iterable


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _set_up_import_path() -> None:
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)


def _load_env() -> None:
    # Optional: supports running script without exporting env vars manually.
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return
    load_dotenv(os.path.join(_project_root(), ".env"))


def _as_set(values: Iterable[str]) -> set[str]:
    return {v.strip().lower() for v in values if v and v.strip()}


def main() -> int:
    _set_up_import_path()
    _load_env()

    from app.core.storage import Storage

    demo_emails = _as_set(
        [
            "amina.admin@appinsnap.com",
            "zain.hr@appinsnap.com",
            "noah.manager@appinsnap.com",
            "ibrahim@appinsnap.com",
        ]
    )

    employees = Storage.load("pet_employees")
    demo_employee_ids = {
        emp_id
        for emp_id, emp in employees.items()
        if isinstance(emp, dict) and str(emp.get("email", "")).strip().lower() in demo_emails
    }

    if demo_employee_ids:
        for emp_id in demo_employee_ids:
            employees.pop(emp_id, None)
        Storage.save("pet_employees", employees)

    evaluations = Storage.load("pet_evaluations")
    eval_ids_to_remove = {
        ev_id
        for ev_id, ev in evaluations.items()
        if isinstance(ev, dict) and str(ev.get("employeeId", "")).strip() in demo_employee_ids
    }
    if eval_ids_to_remove:
        for ev_id in eval_ids_to_remove:
            evaluations.pop(ev_id, None)
        Storage.save("pet_evaluations", evaluations)

    print(
        {
            "removed_employee_ids": sorted(demo_employee_ids),
            "removed_evaluation_ids": sorted(eval_ids_to_remove),
            "storage_backend": "mongo" if os.getenv("USE_MONGO", "true").strip().lower() not in {"0", "false", "no", "off"} and os.getenv("MONGODB_URI") else "file",
            "db": os.getenv("MONGODB_DB", ""),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


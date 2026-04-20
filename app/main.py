import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import AuthConfig
from app.modules.auth.auth import AuthService
from app.modules.auth.router import router as auth_router
from app.modules.departments.router import router as dept_router
from app.modules.pet.router import router as pet_router

# Load environment variables from .env (local dev)
load_dotenv()

app = FastAPI(title="HR Performance Evaluation System", version="1.0.0")

@app.on_event("startup")
def _bootstrap_admins_on_startup():
    # Bootstrap any configured system admins. Safe to call repeatedly.
    AuthService.bootstrap_admins(AuthConfig.admin_emails())

def _split_origins(raw: str) -> list[str]:
    return [o.strip() for o in (raw or "").split(",") if o.strip()]

# CORS:
# - Set FRONTEND_ORIGINS for multiple allowed frontends (comma-separated).
# - FRONTEND_ORIGIN is kept for backward compatibility (single origin).
frontend_origins = _split_origins(os.getenv("FRONTEND_ORIGINS", ""))
if not frontend_origins:
    frontend_origins = _split_origins(os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dept_router)
app.include_router(pet_router)

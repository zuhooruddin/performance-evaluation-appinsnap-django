import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.router import router as auth_router
from app.modules.departments.router import router as dept_router
from app.modules.pet.router import router as pet_router

# Load environment variables from .env (local dev)
load_dotenv()

app = FastAPI(title="HR Performance Evaluation System", version="1.0.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dept_router)
app.include_router(pet_router)

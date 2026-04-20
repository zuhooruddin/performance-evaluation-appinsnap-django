from fastapi import APIRouter, HTTPException, Query
from pydantic import EmailStr

from .auth import (
    AuthService,
    LoginRequest,
    OTPVerifyRequest,
    UserAccessCreate
)

router = APIRouter(prefix="/auth", tags=["Auth & Access"])

@router.post("/bootstrap")
def bootstrap_admin(
    email: EmailStr | None = Query(None),
    name: str | None = Query(None),
):
    try:
        AuthService.bootstrap_admin(email=str(email) if email else None, name=name)
        return {"message": "Admin bootstrapped successfully", "email": str(email) if email else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/register")
def register_user(data: UserAccessCreate):
    try:
        user = AuthService.register_access_profile(data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/restriction")
def toggle_user_restriction(email: EmailStr = Query(...), restrict: bool = Query(...)):
    try:
        return AuthService.toggle_restriction(email, restrict)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/users")
def list_users():
    try:
        return AuthService.list_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(data: LoginRequest):
    try:
        return AuthService.request_login(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify")
def verify_otp(data: OTPVerifyRequest):
    try:
        return AuthService.verify_otp(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session")
def validate_session(token: str = Query(...)):
    try:
        return AuthService.validate_session(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
def logout(token: str = Query(...)):
    try:
        return AuthService.logout(token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
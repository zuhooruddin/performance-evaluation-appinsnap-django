import time
import random
import hashlib
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional

from app.core.config import AuthConfig
from app.core.emailer import send_otp_email
from app.core.storage import Storage
from app.core.id_generator import IDGenerator

# =========================
# Enums & Schemas
# =========================

class SystemRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    HR = "hr"
    EMPLOYEE = "employee"

class UserAccessCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., description="Full name of the user")
    system_role: SystemRole
    
    custom_title: Optional[str] = Field(None, description="e.g., CTO, HR, Line Manager")
    permissions: List[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def enforce_role_rules(self):
        if self.system_role == SystemRole.ADMIN:
            self.permissions = ["ALL"]
            self.custom_title = "System Admin"

        elif self.system_role == SystemRole.MANAGER:
            self.custom_title = self.custom_title or "Line Manager"

        elif self.system_role == SystemRole.HR:
            self.custom_title = self.custom_title or "HR"

        elif self.system_role == SystemRole.EMPLOYEE:
            self.permissions = []
            self.custom_title = None

        return self

class LoginRequest(BaseModel):
    email: EmailStr
    role: str

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=10)

# =========================
# Service Layer
# =========================

class AuthService:

    # --------------------------------
    # Bootstrap Admin
    # --------------------------------
    @staticmethod
    def bootstrap_admin(email: str | None = None, name: str | None = None):
        users = Storage.load("users")
        admin_email = (email or AuthConfig.ADMIN_EMAIL).strip().lower()
        admin_name = (name or "Super Administrator").strip() or "Super Administrator"
        
        # Check if admin email already exists anywhere in the values
        admin_exists = any(u.get("email", "").lower() == admin_email for u in users.values())

        if not admin_exists:
            uid = IDGenerator.generate("ADM")
            users[uid] = {
                "id": uid,
                "email": admin_email,
                "name": admin_name,
                "system_role": SystemRole.ADMIN.value,
                "custom_title": "System Admin",
                "permissions": ["ALL"],
                "is_active": True,
                "created_at": time.time()
            }
            Storage.save("users", users)

    # --------------------------------
    # Register Access Profile
    # --------------------------------
    @staticmethod
    def register_access_profile(data: UserAccessCreate):
        users = Storage.load("users")

        # DYNAMIC UNIQUENESS CHECK: Email + Role + Title
        for u in users.values():
            if u.get("email", "").lower() == data.email.lower() and \
               u.get("system_role") == data.system_role.value and \
               u.get("custom_title") == data.custom_title:
                
                title_desc = f" ({data.custom_title})" if data.custom_title else ""
                raise ValueError(f"Email '{data.email}' already has an active '{data.system_role.value}'{title_desc} profile.")

        prefix = "EMP"
        if data.system_role in (SystemRole.MANAGER, SystemRole.HR):
            prefix = "EVAL"
        if data.system_role == SystemRole.ADMIN: prefix = "ADM"

        uid = IDGenerator.generate(prefix)
        user_profile = {
            "id": uid,
            "email": data.email,
            "name": data.name,
            "system_role": data.system_role.value,
            "custom_title": data.custom_title,
            "permissions": data.permissions,
            "is_active": True,
            "created_at": time.time()
        }
        
        # We now save using the ID as the primary key, not the email!
        users[uid] = user_profile
        Storage.save("users", users)
        return user_profile

    # --------------------------------
    # Toggle Restriction (By Email)
    # --------------------------------
    @staticmethod
    def toggle_restriction(email: str, restrict: bool):
        """Restricts or Activates ALL profiles associated with this email."""
        users = Storage.load("users")
        found = False
        
        for uid, u in users.items():
            if u.get("email", "").lower() == email.lower():
                users[uid]["is_active"] = not restrict
                found = True
                
        if not found:
            raise ValueError("User email not found.")
            
        Storage.save("users", users)
        return {"message": f"All profiles for {email} {'restricted' if restrict else 'activated'} successfully."}

    # --------------------------------
    # Request Login
    # --------------------------------
    @staticmethod
    def request_login(data: LoginRequest):
        users = Storage.load("users")

        # Find ALL profiles for this email that match the requested role
        matching_profiles = [
            u for u in users.values() 
            if u.get("email", "").lower() == data.email.lower() and u.get("system_role", "").lower() == data.role.lower()
        ]

        if not matching_profiles:
            # Figure out exactly why it failed to give a helpful error message
            all_user_profiles = [u for u in users.values() if u.get("email", "").lower() == data.email.lower()]
            if not all_user_profiles:
                raise ValueError("Access Denied: Email not registered in the system.")
            else:
                available_roles = set(u.get("system_role") for u in all_user_profiles)
                raise ValueError(f"Access Denied: You do not have a '{data.role}' profile. Your available roles: {', '.join(available_roles)}")

        if all(not u.get("is_active", True) for u in matching_profiles):
            raise ValueError("Access Denied: Your account has been restricted by Admin.")

        otp = AuthService._generate_otp()
        hashed = AuthService._hash_otp(otp)
        otp_store = Storage.load("otp_store")

        # We save the requested role in the OTP store so the session knows how they logged in
        otp_store[data.email] = {
            "hashed": hashed,
            "role": data.role,
            "expiry": time.time() + AuthConfig.OTP_EXPIRY_SECONDS,
            "attempts": 0
        }
        Storage.save("otp_store", otp_store)

        # Send OTP to email (SMTP)
        send_otp_email(to_email=data.email, otp=otp)

        return {
            "message": "OTP sent successfully"
        }

    # --------------------------------
    # Verify OTP
    # --------------------------------
    @staticmethod
    def verify_otp(data: OTPVerifyRequest):
        otp_store = Storage.load("otp_store")

        if data.email not in otp_store:
            raise ValueError("No OTP requested or OTP expired.")

        record = otp_store[data.email]

        if time.time() > record["expiry"]:
            del otp_store[data.email]
            Storage.save("otp_store", otp_store)
            raise ValueError("OTP expired.")

        if record["attempts"] >= AuthConfig.MAX_OTP_ATTEMPTS:
            del otp_store[data.email]
            Storage.save("otp_store", otp_store)
            raise ValueError("Max attempts exceeded. Request a new OTP.")

        hashed_input = AuthService._hash_otp(data.otp)

        if hashed_input != record["hashed"]:
            record["attempts"] += 1
            Storage.save("otp_store", otp_store)
            raise ValueError("Invalid OTP.")

        # Success! Gather all active profile IDs for this role
        users = Storage.load("users")
        matching_profiles = [
            u for u in users.values()
            if u.get("email", "").lower() == data.email.lower()
            and u.get("system_role", "").lower() == record["role"].lower()
            and u.get("is_active", True)
        ]
        matching_ids = [u["id"] for u in matching_profiles]
        primary_profile = matching_profiles[0] if matching_profiles else None

        token = f"sess_{IDGenerator.generate('TOK')}_{int(time.time())}"
        sessions = Storage.load("sessions")

        sessions[token] = {
            "email": data.email,
            "role": record["role"],
            "profile_ids": matching_ids, # Frontend will receive all active profiles for this role!
            "primary_profile": primary_profile,
            "created_at": time.time()
        }
        Storage.save("sessions", sessions)

        del otp_store[data.email]
        Storage.save("otp_store", otp_store)

        return {
            "message": "Login successful",
            "token": token,
            "user": primary_profile
        }

    # --------------------------------
    # Utilities
    # --------------------------------
    @staticmethod
    def _generate_otp():
        length = AuthConfig.OTP_LENGTH
        start = 10 ** (length - 1)
        end = (10 ** length) - 1
        return str(random.randint(start, end))

    @staticmethod
    def _hash_otp(otp):
        return hashlib.sha256(otp.encode()).hexdigest()
    
    @staticmethod
    def list_users():
        return Storage.load("users")

    @staticmethod
    def validate_session(token):
        sessions = Storage.load("sessions")
        if token not in sessions:
            raise ValueError("Invalid session")
        return sessions[token]

    @staticmethod
    def logout(token):
        sessions = Storage.load("sessions")
        if token not in sessions:
            raise ValueError("Invalid session")
        del sessions[token]
        Storage.save("sessions", sessions)
        return {"message": "Logged out"}
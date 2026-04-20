from dataclasses import dataclass

@dataclass
class AuthConfig:
    # Security Settings
    OTP_EXPIRY_SECONDS: int = 300        # 5 minutes
    MAX_OTP_ATTEMPTS: int = 5            # Fixed name to match auth.py
    OTP_LENGTH: int = 6                  
    LOGIN_RATE_LIMIT_PER_MIN: int = 5    # Added missing rate limit
    SESSION_EXPIRY_SECONDS: int = 86400  # 24 hours

    # Hardcoded System Admin Credentials
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_ROLE: str = "Admin"
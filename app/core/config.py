from dataclasses import dataclass
import os

@dataclass
class AuthConfig:
    # Security Settings
    OTP_EXPIRY_SECONDS: int = 300        # 5 minutes
    MAX_OTP_ATTEMPTS: int = 5            # Fixed name to match auth.py
    OTP_LENGTH: int = 6                  
    LOGIN_RATE_LIMIT_PER_MIN: int = 5    # Added missing rate limit
    SESSION_EXPIRY_SECONDS: int = 86400  # 24 hours

    # System Admin bootstrap emails (comma-separated via env).
    # Values are intentionally resolved from environment at runtime (not import-time)
    # so that `load_dotenv()` in `app/main.py` takes effect.
    ADMIN_EMAIL: str = "admin@company.com"
    ADMIN_EMAILS: str = ""
    ADMIN_ROLE: str = "Admin"

    @staticmethod
    def admin_emails() -> list[str]:
        admin_emails = os.getenv("ADMIN_EMAILS", "").strip()
        admin_email = os.getenv("ADMIN_EMAIL", AuthConfig.ADMIN_EMAIL).strip()

        raw: list[str] = []
        if admin_emails:
            raw.extend(admin_emails.split(","))
        if admin_email:
            raw.append(admin_email)

        out: list[str] = []
        for e in raw:
            e = (e or "").strip().lower()
            if e and e not in out:
                out.append(e)
        return out
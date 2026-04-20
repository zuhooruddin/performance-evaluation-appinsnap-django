import os
import smtplib
from email.message import EmailMessage


def send_otp_email(*, to_email: str, otp: str) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip() or "587")
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM", "").strip() or username
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no", "off"}

    if not host or not from_email:
        raise RuntimeError("SMTP is not configured (SMTP_HOST / SMTP_FROM missing)")

    msg = EmailMessage()
    msg["Subject"] = "Your Performance Evaluation OTP"
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(
        "\n".join(
            [
                "Your One-Time Password (OTP) is:",
                "",
                f"{otp}",
                "",
                "This OTP will expire shortly. If you didn’t request it, you can ignore this email.",
            ]
        )
    )

    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        if use_tls:
            server.starttls()
            server.ehlo()
        if username and password:
            server.login(username, password)
        server.send_message(msg)


from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import SMTP_FROM_EMAIL, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USERNAME, SMTP_USE_TLS


class EmailService:
    @staticmethod
    def send_pin_email(to_email: str, pin: str) -> dict[str, str | bool]:
        message = EmailMessage()
        message["Subject"] = "Your Pesanexa Access PIN"
        message["From"] = SMTP_FROM_EMAIL
        message["To"] = to_email
        message.set_content(
            f"Your Pesanexa PIN is: {pin}\n\n"
            "Use it to complete the authentication flow in the system."
        )

        try:
            if not SMTP_HOST or SMTP_HOST == "localhost":
                return {"success": True, "message": f"Mock email queued for {to_email}. PIN: {pin}"}

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(message)
            return {"success": True, "message": f"PIN email sent to {to_email}."}
        except Exception as exc:  # pragma: no cover - SMTP is external
            return {"success": False, "message": f"Email delivery failed: {exc}"}

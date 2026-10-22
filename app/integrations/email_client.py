from __future__ import annotations

from app.services.email_service import EmailService


class EmailClient:
    @staticmethod
    def send_investor_pin(email: str, pin: str) -> dict[str, str | bool]:
        return EmailService.send_pin_email(email, pin)

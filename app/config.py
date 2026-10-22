from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fms.db")
APP_TITLE = os.getenv("APP_TITLE", "FMS Backend")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "FastAPI backend for the FMS dashboard and auction workflows.",
)
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-me-please-use-32-bytes!",
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "5"))
SESSION_TIMEOUT_SECONDS = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@local.test")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

DEMO_OFFICER_PHONE = os.getenv("DEMO_OFFICER_PHONE", "2547000000000")
DEMO_OFFICER_PIN = os.getenv("DEMO_OFFICER_PIN", "1234")

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:44717101mM?@localhost:5432/pesanexa"
)
APP_TITLE = os.getenv("APP_TITLE", "Pesanexa Backend")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION",
    "FastAPI backend for the Pesanexa dashboard and auction workflows.",
)
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-me-please-use-32-bytes!",
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "20"))
SESSION_TIMEOUT_SECONDS = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "no-reply@local.test")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

DEMO_OFFICER_PHONE = os.getenv("DEMO_OFFICER_PHONE", "254113523551")
DEMO_OFFICER_PIN = os.getenv("DEMO_OFFICER_PIN", "1234")

# Safaricom Daraja M-Pesa configuration
DARAJA_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY", "eY2PfjyhtwMWHYTGbUyN9xzvMTuVtJ6OKFcONGPtjjUNwc4R")
DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET", "5viNZLN2K5O9EYpgsMyWx8v9GgQTOV35ECNN0UTK46nC0nPFCOga36n5iSiRF3iO")
DARAJA_BASE_URL = os.getenv("DARAJA_BASE_URL", "https://sandbox.safaricom.co.ke")
DARAJA_BUSINESS_SHORT_CODE = os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174379")
DARAJA_PASSCODE = os.getenv("DARAJA_PASSCODE", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
DARAJA_INITIATOR_NAME = os.getenv("DARAJA_INITIATOR_NAME", "Pesanexa1")
DARAJA_INITIATOR_PASSWORD = os.getenv("DARAJA_INITIATOR_PASSWORD", "LELmrEKCsi3zWhnLrXIK8xEEcz4y3V2nMO1JLN8COb4MZsPecPQDJXJ0G3XC1v3iZ+SmhLekDuJ5QEly7dV6XAyDhwPoGUacshnlcQoVihwdbi5Jpvilq9ULWqaSGy/pDipVf/MBMcAKAnZGJ8iuOjSLWGIhst6ttT+eNYEwS63wK997wPvNb3Oteto4yQXSTSp+XQydiv+7zfrHnJ0K6eRlBkOXpTKxQiAiRY9+ypgZ2ro2vG09aILpmt25U3Kn5YnUkMEZDzJWu1uRTDb86rvrvschYo9skTpPC1E2mLhttR1lnOESliKQx0S5rtkyJW7U3DhMpbUFAu+SspP88A==")
DARAJA_CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL", "https://your-domain.com/api/v1/daraja/callback")

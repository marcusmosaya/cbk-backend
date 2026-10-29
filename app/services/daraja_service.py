from __future__ import annotations

import base64
import os
import uuid
from datetime import datetime

import requests


class DarajaService:
    """Safaricom Daraja M-Pesa API client."""

    def __init__(
        self,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ):
        self.consumer_key = consumer_key or os.getenv("DARAJA_CONSUMER_KEY", "eY2PfjyhtwMWHYTGbUyN9xzvMTuVtJ6OKFcONGPtjjUNwc4R")
        self.consumer_secret = consumer_secret or os.getenv("DARAJA_CONSUMER_SECRET", "5viNZLN2K5O9EYpgsMyWx8v9GgQTOV35ECNN0UTK46nC0nPFCOga36n5iSiRF3iO")
        self.base_url = (base_url or os.getenv("DARAJA_BASE_URL", "https://sandbox.safaricom.co.ke")).rstrip("/")
        self.timeout = timeout

    def _auth_header(self) -> str:
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        print(f"Daraja auth credentials: {credentials}")  # Debugging line
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def get_access_token(self) -> dict:
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(
                url,
                headers={"Authorization": self._auth_header()},
                timeout=self.timeout,
            )
            data = response.json()
            print(f"Daraja access token response: {data}")  # Debugging line
            return {
                "success": "access_token" in data,
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in"),
                "error": data.get("error"),
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def stk_push(
        self,
        phone: str,
        amount: float,
        account_reference: str,
        transaction_desc: str,
        business_short_code: str | None = None,
        access_token: str | None = None,
    ) -> dict:
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        callback_url = os.getenv("DARAJA_CALLBACK_URL", "https://state-salvage-visa.ngrok-free.dev/api/v1/daraja/callback/stk")
        print(self._normalize_phone(phone), "phone", phone)
        payload = {
            "BusinessShortCode": business_short_code or os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174379"),
            "Password": self._generate_password(business_short_code),
            "Timestamp": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": self._normalize_phone(phone),
            "PartyB": business_short_code or os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174379"),
            "PhoneNumber": self._normalize_phone(phone),
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc,
            "CallBackURL": callback_url,
        }
        if callback_url:
            payload["CallbackURL"] = callback_url
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            print(f"Daraja STK Push response: {response.json()}")  # Debugging lin7
            return response.json()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def stk_query(self, checkout_request_id: str, access_token: str | None = None) -> dict:
        url = f"{self.base_url}/mpesa/stkpush/v1/queryrequest"
        payload = {
            "BusinessShortCode": os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174399"),
            "Password": self._generate_password(),
            "Timestamp": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "CheckoutRequestID": checkout_request_id,
        }
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            return response.json()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def b2c_payout(
        self,
        phone: str,
        amount: float,
        remarks: str,
        access_token: str | None = None,
    ) -> dict:
        url = f"{self.base_url}/mpesa/b2c/v1/request"
        callback_url = os.getenv("DARAJA_CALLBACK_URL", "")
        print(self._normalize_phone(phone),"phone",phone)
        payload = {
            "OriginatorConversationID": f"WSA{uuid.uuid4().hex[:18].upper()}",
            "OriginatorReference": "Pesanexa Withdrawal",
            "InitiatorName": os.getenv("DARAJA_INITIATOR_NAME", "Pesanexa"),
            "SecurityCredential": os.getenv("DARAJA_INITIATOR_PASSWORD", ""),
            "CommandID": "BusinessPayment",
            "SenderIdentifierType": "4",
            "RecieverIdentifierType": "1",
            "Amount": int(amount),
            "PartyA": os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174399"),
            "PartyB": self._normalize_phone(phone),
            "AccountReference": "Pesanexa Wallet",
            "Remarks": remarks,
        }
        if callback_url:
            payload["ResultURL"] = callback_url
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            return response.json()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _generate_password(self, business_short_code: str | None = None) -> str:
        code = business_short_code or os.getenv("DARAJA_BUSINESS_SHORT_CODE", "174379")
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        raw = f"{code}{os.getenv('DARAJA_PASSCODE', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        digits = (phone or "").strip().replace(" ", "").replace("-", "").lstrip("+")
        if digits.startswith("0") and len(digits) == 10:
            return "254" + digits[1:]
        if len(digits) == 9 and digits[0] in "71":
            return "254" + digits
        return digits
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    @staticmethod
    def normalize_phone(raw_phone: str | None) -> str:
        if raw_phone is None:
            return ""
        return str(raw_phone).strip().replace(" ", "").lstrip("+")

    def list_users(self):
        return self.repository.get_all()

    def get_user(self, user_id: int):
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def create_user(self, data: dict):
        phone = self.normalize_phone(data.get("phone"))
        if not phone:
            raise HTTPException(status_code=400, detail="Phone number is required")

        data["phone"] = phone
        data["national_id"] = str(data.get("national_id", "")).strip()
        data["email"] = str(data.get("email", "")).strip().lower()
        data["role"] = str(data.get("role") or "Investor").strip() or "Investor"
        data["active"] = bool(data.get("active", True))

        if self.repository.get_by_phone(phone):
            raise HTTPException(status_code=400, detail="A user with this phone number already exists")
        return self.repository.create(data)

    def update_user(self, user_id: int, data: dict):
        user = self.get_user(user_id)
        if "phone" in data and data["phone"] is not None:
            data["phone"] = self.normalize_phone(data["phone"])
        if "national_id" in data and data["national_id"] is not None:
            data["national_id"] = str(data["national_id"]).strip()
        if "email" in data and data["email"] is not None:
            data["email"] = str(data["email"]).strip().lower()
        if "role" in data and data["role"] is not None:
            data["role"] = str(data["role"]).strip() or "Investor"
        return self.repository.update(user, data)

    def deactivate_user(self, user_id: int):
        user = self.get_user(user_id)
        return self.repository.update(user, {"active": not user.active})

    def delete_user(self, user_id: int):
        user = self.get_user(user_id)
        self.repository.delete(user)
        return {"success": True, "message": "User deleted successfully"}

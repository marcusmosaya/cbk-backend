from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
import re
from app.database import get_or_create_system_account
from app.models.user import User
from app.models.user_account_restriction import UserAccountRestriction
from app.models.user_balance import UserBalance
from app.models.user_transaction import UserTransaction
from app.repositories.ussd_repository import UssdRepository
from app.services.activity_log_service import record_activity


class UssdService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UssdRepository(db)

    @staticmethod
    def normalize_phone(phone: str) -> str:
        digits = (phone or "").strip().replace(" ", "").replace("-", "").lstrip("+")
        if not digits:
            return ""
        
        if digits.startswith("+"):
            digits = digits[1:]

        if re.fullmatch(r"254[17]\d{8}", digits):
            return digits
        
        if re.fullmatch(r"0[17]\d{8}", digits):
            return "254" + digits[1:]
        return digits

    def ensure_default_menus(self) -> list[dict[str, Any]]:
        menus = self.repository.get_menus()
        if menus:
            return [
                {
                    "code": menu.code,
                    "title": menu.title,
                    "description": menu.description,
                    "parent_code": menu.parent_code,
                    "sequence": menu.sequence,
                    "content": menu.content,
                    "is_active": menu.is_active,
                }
                for menu in menus
            ]

        default_menus = [
            {
                "code": "main",
                "title": "Pesanexa USSD",
                "description": "Main menu",
                "sequence": 1,
                "content": "Welcome to Pesanexa\n1. View securities\n2. My balances\n3. My bids\n4. Help",
                "is_active": True,
            },
            {
                "code": "securities",
                "title": "Available securities",
                "description": "List of securities",
                "parent_code": "main",
                "sequence": 2,
                "content": "Available securities\nReply with the security code or 0 to return",
                "is_active": True,
            },
            {
                "code": "help",
                "title": "Help",
                "description": "Usage help",
                "parent_code": "main",
                "sequence": 3,
                "content": "For help, call the officer desk or use the admin portal.",
                "is_active": True,
            },
        ]

        return [
            self.repository.create_menu(menu_data)
            for menu_data in default_menus
        ]

    def list_sessions(self):
        return self.repository.get_sessions()

    def get_session(self, session_id: str):
        session = self.repository.get_session_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="USSD session not found")
        return session

    def get_session_logs(self, session_id: str):
        session = self.get_session(session_id)
        return self.repository.list_logs(session_id=session.id)

    def start_session(self, phone: str, session_id: str | None = None):
        normalized_phone = self.normalize_phone(phone)
        if not normalized_phone:
            raise HTTPException(status_code=400, detail="Phone number is required")

        existing = self.repository.get_active_session_by_phone(normalized_phone)
        if existing is not None and (session_id is None or existing.session_id == session_id):
            return {
                "session_id": existing.session_id,
                "phone": existing.phone,
                "state": existing.state,
                "message": self._build_message(existing, None),
            }

        generated_session_id = session_id or f"ussd-{uuid.uuid4().hex[:12]}"
        session = self.repository.create_session(
            phone=normalized_phone,
            session_id=generated_session_id,
            state="start",
            menu_code="main",
        )
        self.repository.create_log(
            phone=normalized_phone,
            request_data="start",
            response_data=self._build_message(session, None),
            session_id=session.id,
            request_type="session_start",
        )
        return {
            "session_id": session.session_id,
            "phone": session.phone,
            "state": session.state,
            "message": self._build_message(session, None),
        }

    def process_input(self, session_id: str, phone: str, user_input: str):
        session = self.repository.get_session_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="USSD session not found")

        normalized_phone = self.normalize_phone(phone)
        if session.phone != normalized_phone:
            raise HTTPException(status_code=403, detail="Session phone mismatch")

        raw_input = (user_input or "").strip()
        menu_code = session.menu_code or "main"
        next_state = session.state

        if raw_input in {"0", "00"}:
            menu_code = "main"
            next_state = "start"
        elif raw_input == "1":
            menu_code = "securities"
            next_state = "securities"
        elif raw_input == "4":
            menu_code = "help"
            next_state = "help"
        else:
            if menu_code == "securities" and raw_input:
                next_state = "securities_selected"
            elif not raw_input:
                next_state = "start"

        updated_session = self.repository.update_session(
            session,
            state=next_state,
            menu_code=menu_code,
            last_input=raw_input,
        )

        response = self._build_message(updated_session, raw_input)
        self.repository.create_log(
            phone=normalized_phone,
            request_data=raw_input,
            response_data=response,
            session_id=updated_session.id,
            request_type="input",
        )

        return {
            "session_id": updated_session.session_id,
            "phone": updated_session.phone,
            "state": updated_session.state,
            "menu_code": updated_session.menu_code,
            "message": response,
        }

    def list_menus(self):
        self.ensure_default_menus()
        return self.repository.get_menus()

    def create_menu(self, data: dict):
        payload = {
            "code": (data.get("code") or "").strip(),
            "title": (data.get("title") or "").strip(),
            "description": data.get("description"),
            "parent_code": data.get("parent_code"),
            "sequence": int(data.get("sequence", 1)),
            "content": data.get("content"),
            "is_active": bool(data.get("is_active", True)),
        }
        if not payload["code"] or not payload["title"]:
            raise HTTPException(status_code=400, detail="Menu code and title are required")
        return self.repository.create_menu(payload)

    def _log_ussd_action(self, user: User, action: str, description: str, entity_id: int | None = None):
        return record_activity(
            self.db,
            user,
            action=f"ussd_{action}",
            entity_type="ussd",
            entity_id=entity_id,
            description=description,
        )

    def _build_message(self, session, user_input: str | None) -> str:
        menu = self.repository.get_menu_by_code(session.menu_code or "main")
        if menu is not None and menu.content:
            return menu.content
        if user_input is None:
            return "Welcome to Pesanexa USSD. Please select an option.\n1. View securities\n2. My balances\n3. My bids\n4. Help"
        return "Thank you. Your request has been received."

    def handle_request(self, session_id: str | None, service_code: str | None, phone_number: str | None, text: str | None):

        normalized_phone = self.normalize_phone(phone_number or "")
        if not phone_number:
            return "END Invalid phone number.", "phone_error"

        if session_id:
            session = self.repository.get_session_by_id(session_id)
        else:
            session = None

        if session is None:
            session = self.repository.create_session(
                phone=phone_number,
                session_id=session_id or f"ussd-{uuid.uuid4().hex[:12]}",
                state="pin_entry",
                menu_code="pin_entry",
            )

        current_text = (text or "").strip()

        if current_text in {"", "default"}:
            self.repository.update_session(session, state="pin_entry", menu_code="pin_entry", last_input="")
            return "CON Welcome to Pesanexa\nEnter your PIN:", "pin_entry"

        user = self.db.query(User).filter(User.phone == phone_number).first()
        if user is None:
            return "END Phone number not registered.", "phone_error"

        if session.state == "pin_entry":
            if user.pin != current_text:
                self.repository.update_session(session, state="pin_entry", menu_code="pin_entry", last_input=current_text)
                self._log_ussd_action(
                    user,
                    "login_failed",
                    f"{user.name} failed USSD login with an invalid PIN.",
                    entity_id=user.id,
                )
                return "CON Welcome to Pesanexa\nEnter your PIN:\nInvalid PIN. Please try again.", "pin_entry"

            first_name = (user.name or "Customer").split()[0]
            self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=current_text)
            self._log_ussd_action(
                user,
                "login_success",
                f"{user.name} successfully logged in to the USSD portal.",
                entity_id=user.id,
            )
            response = (
                f"CON Dear {first_name}, welcome to Pesanexa\n"
                "1. Balance Enquiry\n"
                "2. My Wallet\n"
                "3. Transaction History\n"
                "4. Account Details\n"
                "5. Contact us\n"
                "98. Others\n"
                "0. exit"
            )
            return response, "main_menu"

        if session.state == "main_menu":
            choice = current_text.strip()

            if choice == "0":
                self.repository.update_session(session, state="exit", menu_code="exit", last_input=choice)
                return "END Thank you for using Pesanexa. Goodbye.", "exit"

            if choice == "1":
                balance_record = self.db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
                balance = float(balance_record.amount) if balance_record else 0.0
                self.repository.update_session(session, state="balance_enquiry", menu_code="balance_enquiry", last_input=choice)
                return f"END Your balance is KES {balance:,.2f}", "balance_enquiry_end"

            if choice == "2":
                self.repository.update_session(session, state="wallet_menu", menu_code="wallet_menu", last_input=choice)
                return "CON My Wallet\n1. Deposit\n2. Transfer\n3. Withdraw\n0. Back", "wallet_menu"

            if choice == "3":
                recent_transactions = (
                    self.db.query(UserTransaction)
                    .filter(UserTransaction.user_id == user.id)
                    .order_by(UserTransaction.created_at.desc())
                    .limit(3)
                    .all()
                )
                if not recent_transactions:
                    self.repository.update_session(session, state="transaction_history", menu_code="transaction_history", last_input=choice)
                    return "END No transaction history available.", "transaction_history_end"

                entries = "\n".join(
                    f"{tx.type.title()}: KES {float(tx.amount):,.2f}"
                    for tx in recent_transactions
                )
                self.repository.update_session(session, state="transaction_history", menu_code="transaction_history", last_input=choice)
                return f"END Recent transactions:\n{entries}", "transaction_history_end"

            if choice == "4":
                self.repository.update_session(session, state="account_details", menu_code="account_details", last_input=choice)
                return (
                    "END "
                    f"Name: {user.name}\n"
                    f"Phone: {user.phone}\n"
                    f"Email: {user.email}\n"
                    f"National ID: {user.national_id}\n"
                ), "account_details_end"

            if choice == "5":
                self.repository.update_session(session, state="contact_us", menu_code="contact_us", last_input=choice)
                return "END Contact us: 254700000000 or support@fms.local", "contact_us_end"

            if choice == "98":
                self.repository.update_session(session, state="others_menu", menu_code="others_menu", last_input=choice)
                return "CON Others\n1. Change PIN\n0. Back", "others_menu"

            return "END Invalid choice.", "invalid_choice"

        if session.state == "wallet_menu":
            choice = current_text.strip()

            if choice == "0":
                self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=choice)
                return (
                    f"CON Dear {(user.name or 'Customer').split()[0]}, welcome to Pesanexa\n"
                    "1. Balance Enquiry\n"
                    "2. My Wallet\n"
                    "3. Transaction History\n"
                    "4. Account Details\n"
                    "5. Contact us\n"
                    "98. Others\n"
                    "0. exit"
                ), "main_menu"

            if choice == "1":
                self.repository.update_session(session, state="wallet_deposit_amount", menu_code="wallet_deposit_amount", last_input="")
                return "CON Enter amount to deposit.\n0. Back", "wallet_deposit_amount"

            if choice == "2":
                self.repository.update_session(session, state="wallet_transfer_phone", menu_code="wallet_transfer_phone", last_input="")
                return "CON Enter recipient phone number.\n0. Back", "wallet_transfer_phone"

            if choice == "3":
                self.repository.update_session(session, state="wallet_withdraw_amount", menu_code="wallet_withdraw_amount", last_input="")
                return "CON Enter amount to withdraw.\n0. Back", "wallet_withdraw_amount"

            return "END Invalid choice.", "invalid_choice"

        if session.state == "wallet_deposit_amount":
            if current_text == "0":
                self.repository.update_session(session, state="wallet_menu", menu_code="wallet_menu", last_input="0")
                return "CON My Wallet\n1. Deposit\n2. Transfer\n3. Withdraw\n0. Back", "wallet_menu"

            try:
                amount = float(current_text)
            except ValueError:
                return "CON Enter amount to deposit.\n0. Back", "wallet_deposit_amount"

            if amount <= 0:
                return "CON Enter amount to deposit.\n0. Back", "wallet_deposit_amount"

            balance_record = self.db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
            if balance_record is None:
                balance_record = UserBalance(user_id=user.id, amount=0.0)
                self.db.add(balance_record)
                self.db.flush()

            system_account = get_or_create_system_account(self.db)
            system_balance_record = self.db.query(UserBalance).filter(UserBalance.user_id == system_account.id).first()
            if system_balance_record is None:
                system_balance_record = UserBalance(user_id=system_account.id, amount=0.0)
                self.db.add(system_balance_record)
                self.db.flush()

            balance_record.amount += amount
            system_balance_record.amount += amount
            self.db.add(
                UserTransaction(
                    user_id=user.id,
                    debit_account_id=system_account.id,
                    credit_account_id=user.id,
                    type="credit",
                    amount=amount,
                    note="Wallet deposit",
                    reference=f"DEPOSIT-{user.id}-{uuid.uuid4().hex[:8]}",
                )
            )
            self.db.add(
                UserTransaction(
                    user_id=system_account.id,
                    debit_account_id=system_account.id,
                    credit_account_id=user.id,
                    type="debit",
                    amount=amount,
                    note=f"System account debited | User account credited {user.id}",
                    reference=f"SYSTEM-DEPOSIT-{user.id}-{uuid.uuid4().hex[:8]}",
                )
            )
            self.db.commit()
            self._log_ussd_action(
                user,
                "deposit",
                f"{user.name} deposited KES {amount:,.2f} via USSD.",
                entity_id=user.id,
            )
            self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=str(amount))
            return f"END Deposit successful. New wallet balance is KES {balance_record.amount:,.2f}.", "wallet_deposit_end"

        if session.state == "wallet_transfer_phone":
            if current_text == "0":
                self.repository.update_session(session, state="wallet_menu", menu_code="wallet_menu", last_input="0")
                return "CON My Wallet\n1. Deposit\n2. Transfer\n3. Withdraw\n0. Back", "wallet_menu"

            recipient_phone = self.normalize_phone(current_text)
            if recipient_phone == normalized_phone:
                return "END You cannot transfer to your own phone number.", "wallet_transfer_error"

            recipient = self.db.query(User).filter(User.phone == recipient_phone).first()
            if recipient is None:
                print(f"Recipient phone number not found: {recipient_phone}")
                return "END Recipient phone number not found.", "wallet_transfer_error"

            self.repository.update_session(session, state="wallet_transfer_amount", menu_code="wallet_transfer_amount", last_input=recipient_phone)
            return f"CON Enter amount to transfer to {recipient_phone}.\n0. Back", "wallet_transfer_amount"

        if session.state == "wallet_transfer_amount":
            if current_text == "0":
                self.repository.update_session(session, state="wallet_menu", menu_code="wallet_menu", last_input="0")
                return "CON My Wallet\n1. Deposit\n2. Transfer\n3. Withdraw\n0. Back", "wallet_menu"

            try:
                amount = float(current_text)
            except ValueError:
                return f"CON Enter amount to transfer to {session.last_input or 'recipient'}.\n0. Back", "wallet_transfer_amount"

            if amount <= 0:
                return f"CON Enter amount to transfer to {session.last_input or 'recipient'}.\n0. Back", "wallet_transfer_amount"

            restriction = self.db.query(UserAccountRestriction).filter(UserAccountRestriction.user_id == user.id).first()
            if restriction and not restriction.can_withdraw:
                reason = restriction.reason or "Withdrawal is restricted by an officer."
                return f"END Transfer blocked. {reason}", "wallet_transfer_blocked"

            source_balance = self.db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
            if source_balance is None:
                source_balance = UserBalance(user_id=user.id, amount=0.0)
                self.db.add(source_balance)
                self.db.flush()

            if source_balance.amount < amount:
                return f"END Insufficient wallet balance. Current balance: KES {source_balance.amount:,.2f}", "wallet_transfer_blocked"

            recipient_phone = session.last_input or ""
            recipient = self.db.query(User).filter(User.phone == recipient_phone).first()
            if recipient is None:
                return "END Recipient phone number not found.", "wallet_transfer_error"

            target_balance = self.db.query(UserBalance).filter(UserBalance.user_id == recipient.id).first()
            if target_balance is None:
                target_balance = UserBalance(user_id=recipient.id, amount=0.0)
                self.db.add(target_balance)
                self.db.flush()

            source_balance.amount -= amount
            target_balance.amount += amount

            transfer_ref = f"TRANSFER-{user.id}-{recipient.id}-{uuid.uuid4().hex[:8]}"
            self.db.add(
                UserTransaction(
                    user_id=user.id,
                    debit_account_id=user.id,
                    credit_account_id=recipient.id,
                    type="debit",
                    amount=amount,
                    note=f"Wallet transfer to {recipient_phone}",
                    reference=transfer_ref,
                )
            )
            self.db.add(
                UserTransaction(
                    user_id=recipient.id,
                    debit_account_id=user.id,
                    credit_account_id=recipient.id,
                    type="credit",
                    amount=amount,
                    note=f"Wallet transfer from {normalized_phone}",
                    reference=transfer_ref,
                )
            )
            self.db.commit()
            self._log_ussd_action(
                user,
                "transfer",
                f"{user.name} transferred KES {amount:,.2f} to {recipient_phone} via USSD.",
                entity_id=user.id,
            )
            self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=str(amount))
            return (
                f"END Transfer of KES {amount:,.2f} to {recipient_phone} successful. "
                f"New wallet balance: KES {source_balance.amount:,.2f}."
            ), "wallet_transfer_end"

        if session.state == "wallet_withdraw_amount":
            if current_text == "0":
                self.repository.update_session(session, state="wallet_menu", menu_code="wallet_menu", last_input="0")
                return "CON My Wallet\n1. Deposit\n2. Transfer\n3. Withdraw\n0. Back", "wallet_menu"

            try:
                amount = float(current_text)
            except ValueError:
                return "CON Enter amount to withdraw.\n0. Back", "wallet_withdraw_amount"

            if amount <= 0:
                return "CON Enter amount to withdraw.\n0. Back", "wallet_withdraw_amount"

            restriction = self.db.query(UserAccountRestriction).filter(UserAccountRestriction.user_id == user.id).first()
            if restriction and not restriction.can_withdraw:
                reason = restriction.reason or "Withdrawal is restricted by an officer."
                return f"END Withdrawal blocked. {reason}", "wallet_withdraw_blocked"

            balance_record = self.db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
            available_balance = float(balance_record.amount) if balance_record else 0.0
            if available_balance < amount:
                return f"END Insufficient wallet balance. Current balance: KES {available_balance:,.2f}", "wallet_withdraw_blocked"

            if balance_record is None:
                balance_record = UserBalance(user_id=user.id, amount=0.0)
                self.db.add(balance_record)
                self.db.flush()

            system_account = get_or_create_system_account(self.db)
            system_balance_record = self.db.query(UserBalance).filter(UserBalance.user_id == system_account.id).first()
            if system_balance_record is None:
                system_balance_record = UserBalance(user_id=system_account.id, amount=0.0)
                self.db.add(system_balance_record)
                self.db.flush()

            balance_record.amount -= amount
            system_balance_record.amount += amount
            self.db.add(
                UserTransaction(
                    user_id=user.id,
                    debit_account_id=user.id,
                    credit_account_id=system_account.id,
                    type="debit",
                    amount=amount,
                    note="Wallet withdrawal",
                    reference=f"WITHDRAW-{user.id}-{uuid.uuid4().hex[:8]}",
                )
            )
            self.db.add(
                UserTransaction(
                    user_id=system_account.id,
                    debit_account_id=user.id,
                    credit_account_id=system_account.id,
                    type="credit",
                    amount=amount,
                    note= f"System account credited | User account {user.id}",
                    reference=f"SYSTEM-WITHDRAW-{user.id}-{uuid.uuid4().hex[:8]}",
                )
            )
            self.db.commit()
            self._log_ussd_action(
                user,
                "withdraw",
                f"{user.name} withdrew KES {amount:,.2f} via USSD.",
                entity_id=user.id,
            )
            self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=str(amount))
            return f"END Withdrawal successful. Remaining wallet balance is KES {balance_record.amount:,.2f}.", "wallet_withdraw_end"

        if session.state == "others_menu":
            choice = current_text.strip()

            if choice == "0":
                self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=choice)
                return (
                    f"CON Dear {(user.name or 'Customer').split()[0]}, welcome to Pesanexa\n"
                    "1. Balance Enquiry\n"
                    "2. My Wallet\n"
                    "3. Transaction History\n"
                    "4. Account Details\n"
                    "5. Contact us\n"
                    "98. Others\n"
                    "0. exit"
                ), "main_menu"

            if choice == "1":
                self.repository.update_session(session, state="change_pin_new", menu_code="change_pin_new", last_input="")
                return "CON Enter new PIN:\n0. Back", "change_pin_new"

            return "END Invalid choice.", "invalid_choice"

        if session.state == "change_pin_new":
            new_pin = current_text.strip()

            if new_pin == "0":
                self.repository.update_session(session, state="others_menu", menu_code="others_menu", last_input="0")
                return "CON Others\n1. Change PIN\n0. Back", "others_menu"

            if len(new_pin) < 4 or not new_pin.isdigit():
                return "CON Enter new PIN:\nPIN must be at least 4 digits or 0 to go back.", "change_pin_new"

            self.repository.update_session(session, state="change_pin_confirm", menu_code="change_pin_confirm", last_input=new_pin)
            return "CON Confirm new PIN:\n0. Back", "change_pin_confirm"

        if session.state == "change_pin_confirm":
            confirmed_pin = current_text.strip()
            pending_pin = session.last_input or ""

            if confirmed_pin == "0":
                self.repository.update_session(session, state="others_menu", menu_code="others_menu", last_input="0")
                return "CON Others\n1. Change PIN\n0. Back", "others_menu"

            if confirmed_pin != pending_pin:
                self.repository.update_session(session, state="change_pin_new", menu_code="change_pin_new", last_input="")
                return "CON PINs do not match.\nEnter new PIN:\n0. Back", "change_pin_new"

            user.pin = confirmed_pin
            self.db.commit()
            self._log_ussd_action(
                user,
                "pin_change",
                f"{user.name} changed their USSD PIN.",
                entity_id=user.id,
            )
            self.repository.update_session(session, state="main_menu", menu_code="main_menu", last_input=confirmed_pin)
            return "END PIN changed successfully.", "pin_changed"

        return "END Invalid session state.", "invalid_state"

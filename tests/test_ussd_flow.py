import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.ussd import handle_ussd_request
from app.database import Base
from app.models.user import User
from app.models.user_balance import UserBalance
from app.services.balance_service import BalanceService
from app.services.ussd_service import UssdService


class UssdFlowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", future=True)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.user = User(
            name="Jane Doe",
            phone="254712345678",
            national_id="123456",
            email="jane@example.com",
            role="Investor",
            active=True,
            pin="1234",
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

    def tearDown(self):
        self.db.close()

    def test_pin_prompt_and_main_menu_flow(self):
        service = UssdService(self.db)

        start = service.start_session("+254712345678")
        self.assertIn("Enter your PIN", start["message"])
        self.assertEqual("pin_entry", start["state"])

        authenticated = service.process_input(start["session_id"], "+254712345678", "1234")
        self.assertIn("Dear Jane", authenticated["message"])
        self.assertIn("Balance Enquiry", authenticated["message"])
        self.assertIn("Funds transfer", authenticated["message"])
        self.assertIn("Contact us", authenticated["message"])

    def test_ussd_request_endpoint_uses_service_code(self):
        response = handle_ussd_request(
            sessionId="session-1",
            serviceCode="*123#",
            phoneNumber="254712345678",
            text="",
            db=self.db,
        )

        self.assertEqual("text/plain", response.media_type)
        self.assertIn("Enter your PIN", response.body.decode())

    def test_change_pin_flow_from_main_menu(self):
        session_id = "session-2"

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "")
        self.assertIn("Enter your PIN", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "1234")
        self.assertIn("98. Others", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "98")
        self.assertIn("1. Change PIN", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "1")
        self.assertIn("Enter new PIN", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "4321")
        self.assertIn("Confirm new PIN", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "4321")
        self.assertIn("PIN changed successfully", response)

        updated_user = self.db.query(User).filter(User.phone == "254712345678").first()
        self.assertEqual("4321", updated_user.pin)

    def test_submenu_back_option_returns_to_main_menu(self):
        session_id = "session-3"

        UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "")
        UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "1234")
        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "2")
        self.assertIn("0. Back", response)

        response, _ = UssdService(self.db).handle_request(session_id, "*123#", "254712345678", "0")
        self.assertIn("98. Others", response)

    def test_balance_service_tracks_real_and_artificial_cash_separately(self):
        service = BalanceService(self.db)

        real_balance = service.adjust_balance(self.user.id, 250.0, transaction_type="credit")
        artificial_balance = service.adjust_balance(self.user.id, 75.0, balance_type="artificial", transaction_type="credit")

        self.assertEqual(250.0, real_balance.amount)
        self.assertEqual(75.0, artificial_balance.artificial_cash)
        self.assertEqual(325.0, artificial_balance.total_amount)

    def test_ussd_restriction_uses_specific_reason_field(self):
        from app.models.user_account_restriction import UserAccountRestriction

        self.db.add(
            UserAccountRestriction(
                user_id=self.user.id,
                can_ussd=False,
                can_login=False,
                reason="General restriction",
                reason_ussd="USSD disabled for security review.",
                reason_login="Login disabled for verification.",
            )
        )
        self.db.commit()

        response, state = UssdService(self.db).handle_request("session-4", "*123#", "254712345678", "")

        self.assertEqual("ussd_blocked", state)
        self.assertIn("USSD disabled for security review.", response)
        self.assertNotIn("General restriction", response)

        response, state = UssdService(self.db).handle_request("session-5", "*123#", "254712345678", "1234")

        self.assertEqual("ussd_blocked", state)
        self.assertIn("Login disabled for verification.", response)

    def test_ussd_transfer_uses_national_id_account_number(self):
        recipient = User(
            name="John Smith",
            phone="254700000001",
            national_id="NAT-654321",
            email="john@example.com",
            role="Investor",
            active=True,
            pin="4321",
        )
        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)

        balance = self.db.query(UserBalance).filter(UserBalance.user_id == self.user.id).first()
        if balance is None:
            balance = UserBalance(user_id=self.user.id, amount=1000.0)
            self.db.add(balance)
        else:
            balance.amount = 1000.0
        self.db.commit()

        service = UssdService(self.db)

        response, state = service.handle_request("transfer-session-1", "*123#", "254712345678", "")
        self.assertIn("Enter your PIN", response)

        response, state = service.handle_request("transfer-session-1", "*123#", "254712345678", "1234")
        self.assertIn("My Wallet", response)
        self.assertIn("2. Transfer", response)

        response, state = service.handle_request("transfer-session-1", "*123#", "254712345678", "2")
        self.assertIn("Enter recipient account number", response)
        self.assertNotIn("phone number", response.lower())

        response, state = service.handle_request("transfer-session-1", "*123#", "254712345678", recipient.national_id)
        self.assertIn("Enter amount to transfer to", response)
        self.assertIn(recipient.national_id, response)


if __name__ == "__main__":
    unittest.main()

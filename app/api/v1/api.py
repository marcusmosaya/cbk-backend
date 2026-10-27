from fastapi import APIRouter

from app.api.v1.endpoints import activity_logs, auth, balances, bids, dashboard, securities, settings, transactions, users, ussd, withdrawals
from app.api.v1.endpoints import daraja_callback

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(securities.router)
api_router.include_router(bids.router)
api_router.include_router(balances.router)
api_router.include_router(transactions.router)
api_router.include_router(settings.router)
api_router.include_router(activity_logs.router)
api_router.include_router(ussd.router)
api_router.include_router(withdrawals.router)
api_router.include_router(daraja_callback.router)

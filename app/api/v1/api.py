from fastapi import APIRouter

from app.api.v1.endpoints import auth, balances, bids, dashboard, securities, settings, transactions, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(users.router)
api_router.include_router(securities.router)
api_router.include_router(bids.router)
api_router.include_router(balances.router)
api_router.include_router(transactions.router)
api_router.include_router(settings.router)

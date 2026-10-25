from __future__ import annotations

import threading
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from app.database import create_tables, get_db, seed_demo_data
from app.repositories.ussd_repository import UssdRepository

app = FastAPI(title=APP_TITLE, version=APP_VERSION, description=APP_DESCRIPTION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def prune_ussd_sessions_loop() -> None:
    while True:
        time.sleep(60)
        db = next(get_db())
        deleted = UssdRepository(db).prune_expired_sessions(max_age_minutes=5)
        if deleted:
            print(f"Pruned {deleted} expired USSD sessions.")


@app.on_event("startup")
def startup_event() -> None:
    create_tables()
    print("Database tables created successfully.")
    db = next(get_db())
    seed_demo_data(db)
    print("Demo data seeded successfully.")
    cleanup_thread = threading.Thread(target=prune_ussd_sessions_loop, daemon=True)
    cleanup_thread.start()


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from app.database import create_tables, get_db, seed_demo_data

app = FastAPI(title=APP_TITLE, version=APP_VERSION, description=APP_DESCRIPTION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    create_tables()
    db = next(get_db())
    seed_demo_data(db)


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

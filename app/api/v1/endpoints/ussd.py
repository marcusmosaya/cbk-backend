from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.common import UssdInput, UssdMenuCreate, UssdSessionStart
from app.services.ussd_service import UssdService

router = APIRouter(prefix="/ussd", tags=["ussd"])


@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).list_sessions()


@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).get_session(session_id)


@router.get("/sessions/{session_id}/logs")
def get_session_logs(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).get_session_logs(session_id)


@router.post("/sessions/start")
def start_session(
    payload: UssdSessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).start_session(payload.phone, payload.session_id)


@router.post("/sessions/{session_id}/input")
def submit_session_input(
    session_id: str,
    payload: UssdInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).process_input(session_id, payload.phone, payload.input)


@router.get("/menus")
def list_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).list_menus()


@router.post("/menus")
def create_menu(
    payload: UssdMenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    return UssdService(db).create_menu(payload.model_dump())


@router.post("/request", response_class=PlainTextResponse)
def handle_ussd_request(
    sessionId: str | None = Form(default=None),
    phoneNumber: str | None = Form(default=None),
    networkCode: str | None = Form(default=None),
    serviceCode: str | None = Form(default=None),
    text: str = Form(default=""),
    db: Session = Depends(get_db),
):

    print(f"Received USSD request: sessionId={sessionId}, phoneNumber={phoneNumber}, networkCode={networkCode}, serviceCode={serviceCode}, text={text}")

    if not sessionId:
        raise HTTPException(
            status_code=400,
            detail="Missing sessionId",
        )
    text_input=text.split("*")[-1]
    response, hop = UssdService(db).handle_request(
        sessionId,
        serviceCode or "",
        phoneNumber or "",
        text_input,
    )

    return PlainTextResponse(
        content=response,
        media_type="text/plain",
    )

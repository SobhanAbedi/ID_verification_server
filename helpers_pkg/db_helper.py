from secrets_pkg.db_secret import *
from models_pkg.models import IDCheckRequest, State  # NEEDED. Don't Remove!
from helpers_pkg import email_helper
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import IntegrityError
from typing import List


def connect_to_db() -> Engine:
    # TODO: Remove echo=True at production
    engine = create_engine(PGSQL_DATABASE_URL, echo=True)
    SQLModel.metadata.create_all(engine)
    return engine


def add_request(engine: Engine, id_check_request: IDCheckRequest) -> str | None:
    try:
        session = Session(engine)
        session.add(id_check_request)
        session.commit()
    except IntegrityError as exc:
        return str(exc.__cause__)
    except:
        return "Unhandled Error"
    return None


def check_request(engine: Engine, natid: str, host: str) -> str:
    reqs: List[IDCheckRequest] = []
    with Session(engine) as session:
        reqs = session.exec(select(IDCheckRequest).where(IDCheckRequest.natid == natid)).all()
    if len(reqs) == 0:
        return "No requests found. Submit Another request please"
    elif len(reqs) > 1:
        # TODO: Error Handling
        return "Unhandled Error"
    if host != reqs[0].ipadd:
        return "You don't have access to this record"
    return str(reqs[0].state)


def get_request(engine: Engine, email: str) -> IDCheckRequest | None:
    reqs: List[IDCheckRequest] = []
    with Session(engine) as session:
        reqs = session.exec(select(IDCheckRequest).where(IDCheckRequest.email == email)).all()
    for req in reqs:
        if req.state == State.RECEIVED:
            return req
    return None


def accept(engine: Engine, request: IDCheckRequest) -> None:
    request.state = State.ACCEPTED
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)
        email_helper.send_email_smtp(request.email, "Accepted")


def decline(engine: Engine, request: IDCheckRequest) -> None:
    request.state = State.DECLINED
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)
        email_helper.send_email_smtp(request.email, "Declined")


def set_verification_state(engine: Engine, request: IDCheckRequest) -> None:
    request.state = State.VERIFYING
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)

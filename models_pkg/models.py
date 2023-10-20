from secrets_pkg.db_secret import PGSQL_NATID_KEY
from typing import Optional
from sqlmodel import Field, SQLModel
import sqlalchemy
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from enum import Enum


class State(Enum):
    RECEIVED = 'received'
    VERIFYING = 'verifying'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'


class IDCheckRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lname: str
    email: str = Field(sa_column=sqlalchemy.Column("email", sqlalchemy.String, unique=True))
    natid: str = Field(sa_column=sqlalchemy.Column(
        EncryptedType(sqlalchemy.Unicode, PGSQL_NATID_KEY, AesEngine, 'pkcs5'),
        unique=True
    ))
    ipadd: str
    img1: str
    img2: str
    state: State = Field(default=State.RECEIVED)

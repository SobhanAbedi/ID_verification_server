from typing import Optional
from sqlmodel import Field, SQLModel


class IDCheckRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lname: str
    email: str
    natid: str
    ipadd: str
    img1: str
    img2: str
    state: str

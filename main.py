from fastapi import FastAPI, UploadFile, Form, Request
from typing import Annotated
from helpers.db_url import SQLALCHEMY_DATABASE_URL
from helpers.models import IDCheckRequest  # NEEDED. Don't Remove!
from sqlmodel import Field, Session, SQLModel, create_engine
app = FastAPI()
# TODO: remove echo=True
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/submit/")
async def submit_req(request: Request, lname: Annotated[str, Form()], email: Annotated[str, Form()], natid: Annotated[str, Form()],
                     img1: UploadFile, img2: UploadFile):
    # print(f'name: {lname}\nmail: {email}')
    # async with aiofiles.open('img1', 'wb') as out_file:
    #     while content := await img1.read(1024):  # async read chunk
    #         await out_file.write(content)  # async write chunk
    return {"message": f"got it {request.client.host}"}

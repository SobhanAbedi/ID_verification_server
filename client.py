from fastapi import FastAPI, UploadFile, Form, Request
from typing import Annotated
from helpers_pkg import db_helper, storage_helper, workqueue_helper
from models_pkg.models import IDCheckRequest
import pathlib
import asyncio

engine = db_helper.connect_to_db()
s3 = storage_helper.connect_to_storage()
channel = workqueue_helper.connect_to_channel()
app = FastAPI()
if None in (engine, s3, channel):
    loop = asyncio.get_running_loop()
    loop.stop()


@app.post("/submit/")
async def submit_req(request: Request, lname: Annotated[str, Form()], email: Annotated[str, Form()],
                     natid: Annotated[str, Form()], img1: UploadFile, img2: UploadFile):
    lname = lname.lower()
    email = email.lower()
    img1_name = f'{email}-{lname}-1{pathlib.Path(img1.filename).suffix.lower()}'
    img2_name = f'{email}-{lname}-2{pathlib.Path(img2.filename).suffix.lower()}'

    db_resp = db_helper.add_request(
        engine,
        IDCheckRequest(lname=lname, email=email, natid=natid, ipadd=request.client.host, img1=img1_name, img2=img2_name)
    )
    if db_resp is not None:
        return {"message": db_resp}

    storage_resp = storage_helper.upload_photos(s3, img1_name, img2_name, img1.file, img2.file)
    if storage_resp is not None:
        return {"message": storage_resp}

    workqueue_helper.publish_task(channel, email)
    return {"message": "Request Submitted"}


@app.get("/status/")
async def submit_req(request: Request, natid: str):
    return {"message": db_helper.check_request(engine, natid, request.client.host)}

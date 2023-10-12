from fastapi import FastAPI, UploadFile, Form, Request
from typing import Annotated
from helpers.db_url import *
from helpers.models import IDCheckRequest  # NEEDED. Don't Remove!
from sqlmodel import Field, Session, SQLModel, create_engine
import boto3
import logging
from botocore.exceptions import ClientError

# TODO: remove echo=True
engine = create_engine(PGSQL_DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

s3r = boto3.resource(
    's3',
    endpoint_url=S3_STORAGE_URL,
    aws_access_key_id=S3_STORAGE_ACC,
    aws_secret_access_key=S3_STORAGE_SEC
)

try:
    s3c = s3r.meta.client
    response = s3c.head_bucket(Bucket=S3_BUCKET_NANE)
    
except ClientError as err:
    status = err.response["ResponseMetadata"]["HTTPStatusCode"]
    errcode = err.response["Error"]["Code"]

    if status == 404:
        try:
            bucket = s3r.Bucket(S3_BUCKET_NANE)
            bucket.create(ACL='private')
        except ClientError as exc:
            logging.error(exc)
    elif status == 403:
        logging.error("Access denied, %s", errcode)
    else:
        logging.exception("Error in request, %s", errcode)

app = FastAPI()


@app.get("/")
async def root():
    # for bucket in s3r.buckets.all():
    #     print(bucket.name)
    return {"message": "Hello World"}


@app.post("/submit/")
async def submit_req(request: Request, lname: Annotated[str, Form()], email: Annotated[str, Form()],
                     natid: Annotated[str, Form()],
                     img1: UploadFile, img2: UploadFile):
    # print(f'name: {lname}\nmail: {email}')
    # async with aiofiles.open('img1', 'wb') as out_file:
    #     while content := await img1.read(1024):  # async read chunk
    #         await out_file.write(content)  # async write chunk
    return {"message": f"got it {request.client.host}"}

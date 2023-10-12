from fastapi import FastAPI, UploadFile, Form, Request
from typing import Annotated
from helpers.db_url import *
from helpers.models import IDCheckRequest  # NEEDED. Don't Remove!
from sqlmodel import Field, Session, SQLModel, create_engine
import boto3
import logging
from botocore.exceptions import ClientError
import pathlib
import filetype


# TODO: remove echo=True
engine = create_engine(PGSQL_DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)

s3 = boto3.resource(
    's3',
    endpoint_url=S3_STORAGE_URL,
    aws_access_key_id=S3_STORAGE_ACC,
    aws_secret_access_key=S3_STORAGE_SEC
)

try:
    s3c = s3.meta.client
    response = s3c.head_bucket(Bucket=S3_BUCKET_NANE)
    
except ClientError as err:
    status = err.response["ResponseMetadata"]["HTTPStatusCode"]
    errcode = err.response["Error"]["Code"]

    if status == 404:
        try:
            bucket = s3.Bucket(S3_BUCKET_NANE)
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
    # TODO: Check the email to be unique
    img1_name = f'{email}-{lname}-1{pathlib.Path(img1.filename).suffix.lower()}'
    img2_name = f'{email}-{lname}-2{pathlib.Path(img2.filename).suffix.lower()}'
    try:
        s3b = s3.Bucket(S3_BUCKET_NANE)
        s3b.put_object(ACL='private', Body=img1.file, Key=img1_name)
        s3b.put_object(ACL='private', Body=img2.file, Key=img2_name)
    except ClientError as e:
        logging.error(e)
    id_check_request = IDCheckRequest(lname=lname, email=email, natid=natid, ipadd=request.client.host,
                                      img1=img1_name, img2=img2_name, state='waiting')
    with Session(engine) as session:
        session.add(id_check_request)
        session.commit()

    return {"message": "Request Submitted"}

from fastapi import FastAPI, UploadFile, Form, Request
from typing import Annotated, List
from secrets_pkg.db_secrets import *
from models_pkg.models import State, IDCheckRequest  # NEEDED. Don't Remove!
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.exc import IntegrityError
import boto3
import logging
from botocore.exceptions import ClientError
import pathlib
import pika

# TODO: Remove echo=True at production
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


connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL_PARAMS))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

app = FastAPI()


@app.get("/")
async def root():
    # TODO: Remove this endpoint at production
    reqs: List[IDCheckRequest] = []
    with Session(engine) as session:
        reqs = session.exec(select(IDCheckRequest)).all()
    return {"Requests": reqs}


@app.post("/submit/")
async def submit_req(request: Request, lname: Annotated[str, Form()], email: Annotated[str, Form()],
                     natid: Annotated[str, Form()], img1: UploadFile, img2: UploadFile):

    img1_name = f'{email}-{lname}-1{pathlib.Path(img1.filename).suffix.lower()}'
    img2_name = f'{email}-{lname}-2{pathlib.Path(img2.filename).suffix.lower()}'

    id_check_request = IDCheckRequest(lname=lname, email=email, natid=natid, ipadd=request.client.host,
                                      img1=img1_name, img2=img2_name)

    try:
        session = Session(engine)
        session.add(id_check_request)
        session.commit()
    except IntegrityError as exc:
        return {"message": str(exc.__cause__)}
    except:
        return {"message": "Unknown Error!"}
    else:
        try:
            s3b = s3.Bucket(S3_BUCKET_NANE)
            s3b.put_object(ACL='private', Body=img1.file, Key=img1_name)
            s3b.put_object(ACL='private', Body=img2.file, Key=img2_name)
        except ClientError as e:
            return {"message": str(e)}

    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=email,
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))

    return {"message": "Request Submitted"}


@app.get("/status/")
async def submit_req(request: Request, natid: str):
    reqs: List[IDCheckRequest] = []
    with Session(engine) as session:
        reqs = session.exec(select(IDCheckRequest).where(IDCheckRequest.natid == natid)).all()
    if len(reqs) == 0:
        return {"message": "No requests found. Submit Another request please"}
    elif len(reqs) > 1:
        # TODO: Error Handling
        return {"message": "Unknown Error!"}
    if request.client.host != reqs[0].ipadd:
        return {"message": "You don't have access to this record"}
    return {"message": reqs[0].state}
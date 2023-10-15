from typing import Annotated, List, Dict
from secrets_pkg.db_secrets import *
from models_pkg.models import State, IDCheckRequest  # NEEDED. Don't Remove!
from sqlmodel import Session, SQLModel, create_engine, select
import boto3
import logging
from botocore.exceptions import ClientError
import pika
import requests
import io
from mypy_boto3_s3.service_resource import Bucket

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
            s3b = s3.Bucket(S3_BUCKET_NANE)
            s3b.create(ACL='private')
        except ClientError as exc:
            logging.error(exc)
    elif status == 403:
        logging.error("Access denied, %s", errcode)
    else:
        logging.exception("Error in request, %s", errcode)

connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL_PARAMS))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def send_email(mail_addr: str, msg: str) -> None:
    print(f"Sending Email to {mail_addr}")
    print(requests.post(
        MAIL_SERVICE_API_URL,
        auth=("api", MAIL_SERVICE_API_KEY),
        data={"from": f"ID Checker <mailgun@{MAIL_SERVICE_DOMAIN}>",
              "to": [mail_addr],
              "subject": "ID Check",
              "text": msg}).json())


def accept(request: IDCheckRequest) -> None:
    request.state = State.ACCEPTED
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)
    send_email(request.email, "Accepted")


def decline(request: IDCheckRequest) -> None:
    request.state = State.DECLINED
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)
    send_email(request.email, "Declined")


def set_verifying_state(request: IDCheckRequest) -> None:
    request.state = State.VERIFYING
    with Session(engine) as session:
        session.add(request)
        session.commit()
        session.refresh(request)


def face_detect(bucket: Bucket, img_key: str) -> [float | None, str | None]:
    img = io.BytesIO()
    bucket.download_fileobj(img_key, img)
    print("Got the image")
    img.seek(0)
    response = requests.post(
        'https://api.imagga.com/v2/faces/detections',
        auth=(IMAGGA_API_KEY, IMAGGA_API_SEC),
        files={'image': img},
        data={'return_face_id': 1}).json()
    print(response)
    if response['status']['type'] != 'success':
        print("Couldn't process request!")
        return None, None
    if len(response['result']['faces']) != 1:
        print("Bad Image")
        return 0, None
    else:
        conf = response['result']['faces'][0]['confidence']
        face_id = response['result']['faces'][0]['face_id']
        print(f'Face Confidence is {conf}')
        return conf, face_id


def delete_images(bucket: Bucket, image_keys: List[str]):
    objs: List[Dict[str, str]] = []
    for key in image_keys:
        objs.append({'Key': key})
    bucket.delete_objects(Delete={'Objects': objs, 'Quiet': True})


def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")
    email = body.decode()

    reqs: List[IDCheckRequest] = []
    request: IDCheckRequest | None = None
    with Session(engine) as session:
        reqs = session.exec(select(IDCheckRequest).where(IDCheckRequest.email == email)).all()
    for req in reqs:
        if req.state == State.RECEIVED:
            request = req
            break

    if request is None:
        print(" [x] Request Invalid")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    img1_add = request.img1
    img2_add = request.img2
    set_verifying_state(request)

    s3b = s3.Bucket(S3_BUCKET_NANE)

    conf_img1, face_id_img1 = face_detect(s3b, img1_add)
    if face_id_img1 is None:
        if conf_img1 is not None and conf_img1 < 60:
            decline(request)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            delete_images(s3b, [img1_add, img2_add])
        return

    conf_img2, face_id_img2 = face_detect(s3b, img2_add)
    if face_id_img2 is None:
        if conf_img2 is not None and conf_img2 < 60:
            decline(request)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            delete_images(s3b, [img1_add, img2_add])
        return

    response = requests.get(
        f'https://api.imagga.com/v2/faces/similarity?face_id={face_id_img1}&second_face_id={face_id_img2}',
        auth=(IMAGGA_API_KEY, IMAGGA_API_SEC)).json()
    print(response)
    if response['status']['type'] != 'success':
        print("Couldn't process request!")
    else:
        faces_similarity = response['result']['score']
        print(f'Face Similarity is {faces_similarity}')
        if faces_similarity < 60:
            decline(request)
        else:
            accept(request)

    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    delete_images(s3b, [img1_add, img2_add])


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
channel.start_consuming()
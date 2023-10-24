from helpers_pkg import db_helper, storage_helper, workqueue_helper, imagga_helper
from mypy_boto3_s3.service_resource import Bucket
import time
import logging


def face_resp_handler(bucket: Bucket, img_add: str, repeat_req: bool) -> str | None:
    conf, face_id = imagga_helper.face_detect(bucket, img_add)
    if face_id is None:
        if conf is None and repeat_req is True:
            return face_resp_handler(bucket, img_add, False)
        else:
            storage_helper.delete_images(bucket, [img_add])
        return None
    storage_helper.delete_images(bucket, [img_add])
    return face_id


def callback(ch, method, properties, body):
    email = body.decode('utf8')
    print(f" [x] Received {email}")

    request = db_helper.get_request(engine, email)
    if request is None:
        print(" [x] Request Invalid")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    db_helper.set_verification_state(engine, request)
    img1_add = request.img1
    img2_add = request.img2

    s3b = storage_helper.get_bucket(s3)
    face_id1 = face_resp_handler(s3b, img1_add, True)
    face_id2 = face_resp_handler(s3b, img2_add, True)
    if None in (face_id1, face_id2):
        db_helper.decline(engine, request)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    similarity = imagga_helper.face_similarity(face_id1, face_id2)
    if similarity is None or similarity < 60:
        db_helper.decline(engine, request)
    else:
        db_helper.accept(engine, request)

    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    storage_helper.delete_images(s3b, [img1_add, img2_add])



logging.log(logging.INFO, " [*] Trying to start worker")
engine = db_helper.connect_to_db()
s3 = storage_helper.connect_to_storage()
channel = workqueue_helper.connect_to_channel()
if None not in (engine, s3, channel):
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    channel.start_consuming()
    logging.log(logging.INFO, " [*] Waiting for messages. To exit press CTRL+C")

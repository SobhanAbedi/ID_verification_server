from secrets_pkg.imagga_secrets import *
from mypy_boto3_s3.service_resource import Bucket
import io
import requests


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


def face_similarity(face_id1: str, face_id2: str) -> float | None:
    response = requests.get(
        f'https://api.imagga.com/v2/faces/similarity?face_id={face_id1}&second_face_id={face_id2}',
        auth=(IMAGGA_API_KEY, IMAGGA_API_SEC)).json()
    print(response)
    if response['status']['type'] != 'success':
        print("Couldn't process request!")
        return None
    faces_similarity = response['result']['score']
    print(f'Face Similarity is {faces_similarity}')
    return faces_similarity

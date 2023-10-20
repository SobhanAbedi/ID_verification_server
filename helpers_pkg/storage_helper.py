from secrets_pkg.db_secret import *
import boto3
import logging
from botocore.exceptions import ClientError
from mypy_boto3_s3.service_resource import S3ServiceResource
from typing import BinaryIO, List, Dict
from mypy_boto3_s3.service_resource import Bucket


def connect_to_storage() -> S3ServiceResource | None:
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
            else:
                return s3
        elif status == 403:
            logging.error("Access denied, %s", errcode)
        else:
            logging.exception("Error in request, %s", errcode)
        return None
    else:
        return s3


def upload_photos(s3: S3ServiceResource, img1_name: str, img2_name: str, img1: BinaryIO, img2: BinaryIO) -> str | None:
    try:
        s3b = s3.Bucket(S3_BUCKET_NANE)
        s3b.put_object(ACL='private', Body=img1, Key=img1_name)
        s3b.put_object(ACL='private', Body=img2, Key=img2_name)
    except ClientError as e:
        return str(e)
    return None


def get_bucket(s3: S3ServiceResource) -> Bucket:
    return s3.Bucket(S3_BUCKET_NANE)


def delete_images(s3b: Bucket, image_keys: List[str]):
    objs: List[Dict[str, str]] = []
    for key in image_keys:
        objs.append({'Key': key})
    s3b.delete_objects(Delete={'Objects': objs, 'Quiet': True})
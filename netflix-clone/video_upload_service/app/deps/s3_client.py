# s3_client.py (under app/deps/)
import boto3
import os
from urllib.parse import urlparse, urlunparse


MINIO_INTERNAL_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_URL")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_PUBLIC_ENDPOINT,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION"),
    config=boto3.session.Config(signature_version="s3v4"),
)

internal_s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_INTERNAL_ENDPOINT,  # ← minio:9000
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION"),
    config=boto3.session.Config(signature_version="s3v4"),
)

BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

def initiate_multipart_upload(key: str):
    response = internal_s3.create_multipart_upload(Bucket=BUCKET_NAME, Key=key)
    return response["UploadId"]

def get_presigned_part_url(key: str, upload_id: str, part_number: int):
    return s3.generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key,
            "UploadId": upload_id,
            "PartNumber": part_number
        },
        ExpiresIn=1800
    )


def complete_multipart_upload(key: str, upload_id: str, parts: list):
    return internal_s3.complete_multipart_upload(
        Bucket=BUCKET_NAME,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts}
    )

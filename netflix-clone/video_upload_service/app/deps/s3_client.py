# s3_client.py (under app/deps/)
import os
import boto3
from botocore.exceptions import ClientError
from core.logger import get_logger

MINIO_INTERNAL_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_URL")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")



logger = get_logger("s3_client")

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


def ensure_bucket_exists():
    if not BUCKET_NAME:
        logger.error("MINIO_BUCKET_NAME is not configured")
        raise RuntimeError("MINIO_BUCKET_NAME is not configured")

    try:
        internal_s3.head_bucket(Bucket=BUCKET_NAME)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code in ("404", "NoSuchBucket", "NotFound"):
            logger.info(f"Bucket '{BUCKET_NAME}' does not exist. Creating it...")
            internal_s3.create_bucket(Bucket=BUCKET_NAME)
            logger.info(f"Bucket '{BUCKET_NAME}' created successfully.")
        else:
            raise

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

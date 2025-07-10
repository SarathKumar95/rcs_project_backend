import boto3
import os
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()

# ENV
endpoint = os.getenv("MINIO_ENDPOINT")               # internal Docker DNS
public_url = os.getenv("MINIO_PUBLIC_URL")           # what React/browser will use
access_key = os.getenv("MINIO_ACCESS_KEY")
secret_key = os.getenv("MINIO_SECRET_KEY")
bucket = os.getenv("MINIO_BUCKET_NAME")
region = os.getenv("AWS_REGION")

# Parse internal MinIO endpoint
parsed_internal = urlparse(endpoint)
internal_host = parsed_internal.netloc
parsed_public = urlparse(public_url)
public_host = parsed_public.netloc

# Setup boto3
s3 = boto3.client(
    "s3",
    endpoint_url=f"{parsed_internal.scheme}://{internal_host}",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=region,
)

def ensure_bucket():
    buckets = s3.list_buckets()["Buckets"]
    if not any(b["Name"] == bucket for b in buckets):
        s3.create_bucket(Bucket=bucket)

# Used by React client
def get_presigned_upload_url(object_key: str, expires_in=1800) -> str:
    ensure_bucket()

    signed_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in
    )

    parsed_url = urlparse(signed_url)
    if internal_host in parsed_url.netloc:
        # swap internal Docker hostname with external/public one
        signed_url = urlunparse(parsed_url._replace(netloc=public_host))

    return signed_url

# Internal use — use inside backend only if ever needed
def get_internal_presigned_url(object_key: str, expires_in=1800) -> str:
    ensure_bucket()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_in
    )

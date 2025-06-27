from minio import Minio
from datetime import timedelta
from urllib.parse import urlparse
import os

# Load environment
MINIO_INTERNAL_ENDPOINT = os.getenv("MINIO_INTERNAL_ENDPOINT")  # e.g. minio:9000
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_URL")  # e.g. http://localhost:9000
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")
SECURE = False

# Parse internal host
parsed = urlparse(f"//{MINIO_INTERNAL_ENDPOINT}", scheme="http")
MINIO_HOST = parsed.netloc or parsed.path

# Public host (just hostname:port, no scheme)
PUBLIC_HOST = MINIO_PUBLIC_ENDPOINT.replace("http://", "").replace("https://", "")

# Client for backend to MinIO
minio_client = Minio(
    endpoint=MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=SECURE
)

# Utility: Create bucket if not exists
def ensure_bucket():
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)

# Utility: Get public presigned upload URL
def get_presigned_upload_url(object_name: str) -> str:
    ensure_bucket()

    internal_url = minio_client.presigned_put_object(
        bucket_name=BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(minutes=30)
    )

    internal_host = urlparse(internal_url).netloc
    return internal_url.replace(internal_host, PUBLIC_HOST)

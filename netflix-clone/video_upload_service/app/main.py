from fastapi import FastAPI
from app.routes.video_upload_routes import router as video_upload_router
from app.deps.minio_client import minio_client

app = FastAPI()

@app.get("/buckets")
def list_buckets():
    return [bucket.name for bucket in minio_client.list_buckets()]


app.include_router(video_upload_router, prefix="/videos")
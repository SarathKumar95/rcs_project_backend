from fastapi import FastAPI
from app.routes.video_upload_routes import router as video_upload_router
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from app.deps.s3_client import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket_exists()
    yield

app = FastAPI(lifespan=lifespan, title="Video Upload Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(video_upload_router, prefix="/videos")
from fastapi import FastAPI
from app.routes.video_upload_routes import router as video_upload_router

app = FastAPI()




app.include_router(video_upload_router, prefix="/videos")
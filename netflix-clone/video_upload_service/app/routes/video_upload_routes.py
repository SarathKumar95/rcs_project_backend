from fastapi import APIRouter, HTTPException, Depends
from app.deps.s3_client import (
    initiate_multipart_upload,
    get_presigned_part_url,
    complete_multipart_upload
)
from app.schemas.video_upload import *
from app.utility.videos_db import create_video, update_video_status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db

from app.deps.s3_client import BUCKET_NAME

router = APIRouter()

@router.post("/initiate-upload")
async def initiate_upload(payload: InitiateUploadRequest):
    key = f"uploads/{payload.filename}"
    upload_id = initiate_multipart_upload(key)
    return {"upload_id": upload_id, "key": key}


@router.post("/get-upload-url")
async def get_upload_url(payload: GetUploadUrlRequest):
    url = get_presigned_part_url(
        payload.key,
        payload.upload_id,
        payload.part_number
    )
    return {"url": url}


@router.post("/complete-upload")
async def complete_upload(payload: CompleteUploadRequest, db: AsyncSession = Depends(get_async_db)):
    try:
        result = complete_multipart_upload(
            payload.key,
            payload.upload_id,
            [part.dict() for part in payload.parts]  # boto3 needs list of dicts
        )

        # create a new video entry in the database
        new_video_entry = await create_video(
            VideoCreate(
                title=payload.key.split('/')[-1],  # use filename as title
                description="",
                file_path=f"{BUCKET_NAME}/{payload.key}"
            ),
            db 
        )

        # if create_video returns a success response, update the video status
        if new_video_entry["success"]:
            return {"message": "Upload complete", "result": result}
    
        else:
            # log the error or handle it as needed
            print(f"Failed to create video entry: {new_video_entry['message']}")
            raise HTTPException(status_code=500, detail="Failed to create video entry in database")
    
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error completing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

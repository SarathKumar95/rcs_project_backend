import os
from fastapi import APIRouter, HTTPException, Depends, Header
from app.deps.s3_client import (
    initiate_multipart_upload,
    get_presigned_part_url,
    complete_multipart_upload
)
from app.schemas.video_upload import *
from app.utility.videos_db import create_video, update_video_record
from app.db.session import get_async_db
from app.deps.s3_client import BUCKET_NAME

from sqlalchemy.ext.asyncio import AsyncSession
from core.redis_stream import RedisStreamClient


redis_client = RedisStreamClient()

router = APIRouter()


INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def verify_internal_api(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")



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
            [part.dict() for part in payload.parts],
        )

        # create a new video entry in the database
        new_video_entry = await create_video(
            VideoCreate(
                title=payload.key.split('/')[-1],  # use filename as title
                description="",
                file_path=f"{BUCKET_NAME}/{payload.key}",
                created_by=payload.created_by
            ),
            db 
        )

        # if create_video returns a success response, update the video status
        if new_video_entry["success"]:
            # print(f"Created new video entry with ID: {new_video_entry['video_id']} and result are {result}")

            event = {
                "event": "video_uploaded",
                "video_id": str(new_video_entry['video_id']),
                "location": result["Location"],
                "bucket": result["Bucket"],
                "key": result["Key"],
                "status": "uploaded"
            }

            redis_client.publish(event)

            print(f"Published event to Redis for video ID: {new_video_entry['video_id']}")

            return {"message": "Upload complete", "result": result}
    
        else:
            # log the error or handle it as needed
            print(f"Failed to create video entry: {new_video_entry['message']}")
            raise HTTPException(status_code=500, detail="Failed to create video entry in database")
    
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error completing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# route to update video record
@router.post("/internal/post-transcode-update", dependencies=[Depends(verify_internal_api)])
async def update_video_record_API(payload: Update_Video_Record, db: AsyncSession = Depends(get_async_db)):
    update_result = await update_video_record(payload.video_id, payload.hls_path, payload.upload_status, db)
    if update_result["success"]:

        # log the video update
        print(f"Updated video ID {payload.video_id} with hls_path: {payload.hls_path} and upload_status: {payload.upload_status}")

        return {"message": "Video status updated successfully"}
    else:
        raise HTTPException(status_code=404, detail=update_result["message"])
    

@router.get("/", summary="List all videos in the database")
async def get_all_videos(db: AsyncSession = Depends(get_async_db)):
    from app.utility.videos_db import list_videos
    result = await list_videos(db)
    if result["success"]:
        return {"videos": result["videos"]}
    else:
        raise HTTPException(status_code=500, detail=result["message"])

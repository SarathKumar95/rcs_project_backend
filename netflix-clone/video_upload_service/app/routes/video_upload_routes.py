from fastapi import APIRouter, HTTPException
from app.deps.s3_client import (
    initiate_multipart_upload,
    get_presigned_part_url,
    complete_multipart_upload
)
from app.schemas.video_upload import *

router = APIRouter()

@router.post("/videos/initiate-upload")
async def initiate_upload(payload: InitiateUploadRequest):
    key = f"uploads/{payload.filename}"
    upload_id = initiate_multipart_upload(key)
    return {"upload_id": upload_id, "key": key}


@router.post("/videos/get-upload-url")
async def get_upload_url(payload: GetUploadUrlRequest):
    url = get_presigned_part_url(
        payload.key,
        payload.upload_id,
        payload.part_number
    )
    return {"url": url}


@router.post("/videos/complete-upload")
async def complete_upload(payload: CompleteUploadRequest):
    try:
        result = complete_multipart_upload(
            payload.key,
            payload.upload_id,
            [part.dict() for part in payload.parts]  # boto3 needs list of dicts
        )
        return {"message": "Upload complete", "result": result}
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error completing upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from app.deps.s3_client import get_presigned_upload_url
from app.schemas.video_upload import UploadChunkRequest  # You already have this

router = APIRouter()

@router.post("/upload-chunk")
async def get_chunk_url(payload: UploadChunkRequest):
    object_key = f"{payload.upload_id}/{payload.chunk_index}"
    try:
        url = get_presigned_upload_url(object_key)
        return {"url": url}
    except Exception as e:
        print("Error generating presigned URL:", e)
        raise HTTPException(status_code=500, detail="Presigned URL generation failed")

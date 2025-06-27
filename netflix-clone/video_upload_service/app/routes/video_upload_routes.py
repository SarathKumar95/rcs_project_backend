from fastapi import APIRouter, HTTPException
from app.schemas.video_upload import UploadChunkRequest  # your Pydantic model
from app.deps.minio_client import get_presigned_upload_url


router = APIRouter()



@router.post("/upload-chunk")
async def get_presigned_chunk_url(payload: UploadChunkRequest):
    object_name = f"{payload.upload_id}/{payload.chunk_index}"

    try:
        url = get_presigned_upload_url(object_name)
        return {"url": url}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")

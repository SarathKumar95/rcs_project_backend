import os
from fastapi import APIRouter, HTTPException, Depends, Header
from uuid import UUID
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.s3_client import (
    initiate_multipart_upload,
    get_presigned_part_url,
    complete_multipart_upload
)
from app.schemas.video_upload import *
from app.utility.videos_db import create_video, update_video_record
from app.db.session import get_async_db
from app.deps.s3_client import BUCKET_NAME
from core.auth.dependencies import require_admin, require_authenticated_user
from core.auth.identity import AuthenticatedUser


from core.redis_stream import RedisStreamClient
from app.utility.videos_db import list_videos


from app.utility.videos_db import list_videos, get_video_by_id
from app.utility.video_playback import get_hls_object
from botocore.exceptions import ClientError


redis_client = RedisStreamClient()

router = APIRouter()


INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

async def verify_internal_api(x_internal_api_key: str = Header(...)):
    if x_internal_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")



@router.post("/initiate-upload", dependencies=[Depends(require_admin)])
async def initiate_upload(payload: InitiateUploadRequest):
    key = f"uploads/{payload.filename}"
    upload_id = initiate_multipart_upload(key)
    return {"upload_id": upload_id, "key": key}


@router.post("/get-upload-url", dependencies=[Depends(require_admin)])
async def get_upload_url(payload: GetUploadUrlRequest):
    url = get_presigned_part_url(
        payload.key,
        payload.upload_id,
        payload.part_number
    )
    return {"url": url}


@router.post("/complete-upload")
async def complete_upload(
    payload: CompleteUploadRequest,
    user: AuthenticatedUser = Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        result = complete_multipart_upload(
            payload.key,
            payload.upload_id,
            [part.dict() for part in payload.parts],
        )

        # create a new video entry in the database
        new_video_entry = await create_video(
            VideoCreate(
                title=payload.title,  # use filename as title
                description=payload.description,
                file_path=f"{BUCKET_NAME}/{payload.key}",
                created_by=user.id
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
    


# will eventually move to another service, but for now, we can keep it here for testing purposes

@router.get(
    "/",
    summary="List all videos in the database",
    dependencies=[Depends(require_authenticated_user)],
)
async def get_all_videos(db: AsyncSession = Depends(get_async_db)):
    
    result = await list_videos(db)
    if result["success"]:
        return {"videos": result["videos"]}
    else:
        raise HTTPException(status_code=500, detail=result["message"])



@router.get(
    "/{video_id}/stream/{file_path:path}",
    summary="Stream an HLS playlist or segment",
)
async def stream_video(
    video_id: UUID,
    file_path: str,
    db: AsyncSession = Depends(get_async_db),
    user: AuthenticatedUser = Depends(require_authenticated_user),
):
    """
    Serves HLS files stored in MinIO.

    The master playlist, variant playlists, and media segments all use this
    route. Relative paths inside the HLS playlists resolve under the same
    /stream/ URL, so the playlists do not need to be rewritten.
    """
    video_result = await get_video_by_id(video_id, db)
    if not video_result["success"]:
        raise HTTPException(status_code=404, detail="Video not found")

    video = video_result["video"]

    if video.is_deleted:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.upload_status != 2 or not video.hls_path:
        raise HTTPException(status_code=409, detail="Video is not ready for playback")

    try:
        object_response = get_hls_object(video.hls_path, file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="HLS file not found")
    except ClientError:
        raise HTTPException(status_code=502, detail="Unable to retrieve video content")

    filename = file_path.rsplit("/", 1)[-1].lower()
    if filename.endswith(".m3u8"):
        media_type = "application/vnd.apple.mpegurl"
    elif filename.endswith(".ts"):
        media_type = "video/mp2t"
    elif filename.endswith(".mp4"):
        media_type = "video/mp4"
    else:
        media_type = "application/octet-stream"

    body = object_response["Body"]

    def stream_chunks():
        try:
            for chunk in body.iter_chunks(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk
        finally:
            body.close()

    headers = {"Cache-Control": "private, max-age=60"}
    content_length = object_response.get("ContentLength")
    if content_length is not None:
        headers["Content-Length"] = str(content_length)

    return StreamingResponse(
        stream_chunks(),
        media_type=media_type,
        headers=headers,
    )

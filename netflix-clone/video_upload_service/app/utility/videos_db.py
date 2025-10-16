# service functions for video management

from typing import Optional
from app.models.videos import Video, UploadStatusEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select



from app.schemas.video_upload import VideoCreate


# create a new video entry
async def create_video(video_data: VideoCreate, db: AsyncSession):
    try:
        new_video = Video(
            title=video_data.title,
            description=video_data.description,
            original_file_path=video_data.file_path,
            upload_status=UploadStatusEnum.pending.value,
            created_by=video_data.created_by
        )
        db.add(new_video)
        await db.commit()
        await db.refresh(new_video)

        return {
            "success": True,
            "video_id": new_video.id,
            "message": "Video created successfully"
        }

    except Exception as e:
        await db.rollback()
        # replace print later with structured logging
        print(f"Error creating video: {e}")
        return {
            "success": False,
            "video_id": None,
            "message": str(e)
        }


# read videos
async def get_video_by_id(video_id: int, db: AsyncSession):
    try:
        video = await db.get(Video, video_id)
        if not video:
            return {"success": False, "video": None, "message": "Video not found"}

        return {"success": True, "video": video, "message": "Video fetched successfully"}

    except Exception as e:
        print(f"Error fetching video: {e}")
        return {"success": False, "video": None, "message": str(e)}


async def list_videos(db: AsyncSession, user_id: Optional[int] = None):
    try:
        stmt = select(Video)
        if user_id:
            stmt = stmt.where(Video.user_id == user_id)

        result = await db.execute(stmt)
        videos = result.scalars().all()  # Extract ORM objects

        return {
            "success": True,
            "videos": videos,
            "message": "Videos fetched successfully"
        }

    except Exception as e:
        print(f"Error listing videos: {e}")
        return {
            "success": False,
            "videos": [],
            "message": str(e)
        }


# update video status

async def update_video_status(video_id: int, status: str, db: AsyncSession):
    try:
        video = await db.get(Video, video_id)
        if not video:
            return {"success": False, "video": None, "message": "Video not found"}

        video.status = status
        await db.commit()
        await db.refresh(video)

        return {"success": True, "video": video, "message": f"Video status updated to {status}"}

    except Exception as e:
        await db.rollback()
        print(f"Error updating status: {e}")
        return {"success": False, "video": None, "message": str(e)}
    

# update video with hls_path, upload_status
async def update_video_record(video_id: int, hls_path: str, upload_status: str, db: AsyncSession):
    try:
        video = await db.get(Video, video_id)
        if not video:
            return {"success": False, "message": "Video not found"}

        video.hls_path = hls_path
        video.upload_status = upload_status

        await db.commit()
        await db.refresh(video)

        return {"success": True, "message": "Video status updated successfully", "video": video}

    except Exception as e:
        await db.rollback()
        print(f"Error updating video status: {e}")
        return {"success": False, "message": str(e)}

# delete video
async def delete_video(video_id: int, db: AsyncSession):
    try:
        video = await db.get(Video, video_id)
        if not video:
            return {"success": False, "message": "Video not found"}

        # Soft delete instead of hard delete
        video.is_deleted = True
        await db.commit()
        await db.refresh(video)

        return {"success": True, "message": "Video marked as deleted. Will be hard deleted in 30 days."}

    except Exception as e:
        await db.rollback()
        print(f"Error deleting video: {e}")
        return {"success": False, "message": str(e)}

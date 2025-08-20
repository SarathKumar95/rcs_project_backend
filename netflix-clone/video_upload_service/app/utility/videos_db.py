# service functions for video management

from typing import Optional
from app.models.videos import Video
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_async_db
from sqlalchemy import select


from app.schemas.video_upload import VideoCreate, VideoUpdate


# create a new video entry
async def create_video(video_data: VideoCreate, db: AsyncSession):
    try:
        new_video = Video(
            title=video_data.title,
            description=video_data.description,
            file_path=video_data.file_path,
            status="uploaded",
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
        query = db.query(Video)
        if user_id:
            query = query.filter(Video.user_id == user_id)
        videos = await query.all()
        return {"success": True, "videos": videos, "message": "Videos fetched successfully"}

    except Exception as e:
        print(f"Error listing videos: {e}")
        return {"success": False, "videos": [], "message": str(e)}


# update video details

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

from core.redis_stream import RedisStreamClient
from core.logger import get_logger
from app.ffmpeg_runner import transcode_video


logger = get_logger("video_transcoding")
redis_client = RedisStreamClient(stream_name="video_events")

def listen_for_videos():
    event = redis_client.listen(block_ms=5000)
    if not event:
        return

    data = event["data"]
    event_type = data.get("event")

    # log the data 
    logger.info(f"Received event: {data}")

    if event_type == "video_uploaded":
        video_id = data["video_id"]
        file_path = data["key"]

        logger.info(f"[{video_id}] 🎬 Starting transcoding for file: {file_path}")

        logger.info(f"[{video_id}]  Received upload event. Starting transcoding...")
        transcode_video(video_id, file_path)

from core.redis_stream import redis_client
from core.logger import get_logger
from app.ffmpeg_runner import transcode_video



logger = get_logger("video_transcoding")

CONSUMER_GROUP = "transcoding_group"
CONSUMER_NAME = "transcoding-worker-1"


def initialize_consumer_group():
    redis_client.ensure_consumer_group(CONSUMER_GROUP)


def listen_for_videos():
    message = redis_client.listen(
        group_name=CONSUMER_GROUP,
        consumer_name=CONSUMER_NAME,
        block_ms=5000,
    )

    if message is None:
        return

    message_id = message["id"]
    data = message["data"]

    logger.info("Received Redis message %s: %s", message_id, data)

    event_type = data.get("event")

    if event_type != "video_uploaded":
        logger.warning(
            "Unsupported event type %r; message %s remains pending",
            event_type,
            message_id,
        )
        return

    # Missing required fields will raise an exception.
    video_id = data["video_id"]
    file_path = data["key"]

    logger.info(
        "[%s] Starting transcoding for file: %s",
        video_id,
        file_path,
    )

    # If this raises an exception, XACK is not executed.
    transcode_video(video_id, file_path)

    # Acknowledge only after processing returns successfully.
    acknowledged = redis_client.acknowledge(
        group_name=CONSUMER_GROUP,
        message_id=message_id,
    )

    if acknowledged != 1:
        logger.error(
            "[%s] Failed to acknowledge message %s; XACK result: %s",
            video_id,
            message_id,
            acknowledged,
        )

        raise RuntimeError(
            f"[{video_id}] Failed to acknowledge message {message_id}; XACK result: {acknowledged}"
        )

    logger.info(
        "[%s] Transcoding completed; XACK result: %s",
        video_id,
        acknowledged,
    )

from core.redis_stream import redis_client
from core.logger import get_logger
from app.ffmpeg_runner import transcode_video



logger = get_logger("video_transcoding")

CONSUMER_GROUP = "transcoding_group"
CONSUMER_NAME = "transcoding-worker-1"


def initialize_consumer_group():
    redis_client.ensure_consumer_group(CONSUMER_GROUP)


def process_message(message):
    message_id = message["id"]
    data = message["data"]

    if data.get("event") != "video_uploaded":
        logger.error(
            "Unsupported event type: %s",
            data.get("event"),
        )
        return

    video_id = data["video_id"]
    file_key = data["key"]

    logger.info(
        "[%s] Starting transcoding for %s",
        video_id,
        file_key,
    )

    # If this raises an exception, do not acknowledge the message.
    transcode_video(video_id, file_key)

    acknowledged = redis_client.acknowledge(
        group_name=CONSUMER_GROUP,
        message_id=message_id,
    )

    if acknowledged != 1:
        raise RuntimeError(
            f"Failed to acknowledge Redis message {message_id}"
        )

    logger.info(
        "[%s] Transcoding completed and message acknowledged",
        video_id,
    )



def listen_for_videos():
    message = redis_client.listen(
        group_name=CONSUMER_GROUP,
        consumer_name=CONSUMER_NAME,
        block_ms=5000,
    )

    if message is None:
        logger.debug("No new messages received from Redis stream")
        return

    logger.info(
        "Received Redis message %s",
        message["id"],
    )

    process_message(message)

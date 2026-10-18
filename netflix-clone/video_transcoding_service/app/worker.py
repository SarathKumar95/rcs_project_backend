import time
from app.redis_listener import listen_for_videos
from core.logger import get_logger
from core.redis_stream import redis_client



logger = get_logger("video_transcoding")

def start_worker():
    logger.info("Transcoding worker started, checking if redis connection is active ...")

    try:
        redis_active = redis_client.check_connection()

        if redis_active:
            


    while True:
        try:
            listen_for_videos()
            # time.sleep(1) 
        except KeyboardInterrupt:
            logger.warning(" Worker stopped manually.")
            break
        except Exception as e:
            logger.exception(f" Worker error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    start_worker()
from app.redis_listener import listen_for_videos
from core.logger import get_logger
import time


logger = get_logger("video_transcoding")

def start_worker():
    logger.info("Transcoding worker started, listening for Redis events...")
    while True:
        try:
            listen_for_videos()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.warning(" Worker stopped manually.")
            break
        except Exception as e:
            logger.error(f" Worker error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    start_worker()
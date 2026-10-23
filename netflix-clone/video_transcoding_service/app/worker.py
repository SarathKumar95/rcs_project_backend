import time
from app.redis_listener import listen_for_videos,initialize_consumer_group, process_message, CONSUMER_GROUP, CONSUMER_NAME
from core.logger import get_logger
from core.redis_stream import redis_client


logger = get_logger("video_transcoding")


CLAIM_IDLE_MS = 5 * 60 * 1000
CLAIM_BATCH_SIZE = 10



def start_worker():
    logger.info("Transcoding worker started, checking if redis connection is active ...")

    claim_cursor = "0-0"

    try:
        redis_client.check_connection()
        initialize_consumer_group()

    except KeyboardInterrupt:
        logger.warning("Worker startup interrupted")
        return
        
    except Exception:
        logger.exception("Worker startup failed")
        raise


    logger.info("Worker is now listening for video upload events ...")


    while True:
        try:
            # 1. Look for old pending messages
            next_cursor, claimed = redis_client.claim_pending(
                group_name=CONSUMER_GROUP,
                consumer_name=CONSUMER_NAME,
                min_idle_time_ms=CLAIM_IDLE_MS,
                start_id=claim_cursor,
                count=CLAIM_BATCH_SIZE,
            )

            claim_cursor = next_cursor

            # 2. Process recovered messages first
            if claimed:
                logger.info(
                    "Processing %d claimed pending messages",
                    len(claimed),
                )
                for message in claimed:
                    process_message(message)
                continue

            # 3. No eligible pending messages:
            logger.debug("No pending messages to claim, waiting for new events ...")
            # wait for a new event
            listen_for_videos()

        except KeyboardInterrupt:
            logger.warning("Worker stopped manually")
            break

        except Exception:
            logger.exception("Worker error")
            time.sleep(2)

if __name__ == "__main__":
    start_worker()
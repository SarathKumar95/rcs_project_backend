import os
import redis
from typing import Dict
from redis.exceptions import ResponseError
from core.logger import get_logger

logger = get_logger("redis_stream")


class RedisStreamClient:
    def __init__(
            self,
            host: str = None,
            port: int = None,
            stream_name: str = None
        ):
            self.host = host or os.getenv("REDIS_HOST", "localhost")
            self.port = int(port or os.getenv("REDIS_PORT", 6379))
            self.stream_name = stream_name or os.getenv("REDIS_STREAM_NAME", "video_events")

            self.client = redis.Redis(host=self.host, port=self.port, decode_responses=True)


    def check_connection(self) -> None:
        try:
            self.client.ping()
            logger.info("Redis connection successful")
        except redis.exceptions.RedisError:
            logger.exception("Unable to connect to Redis")
            raise

    def ensure_consumer_group(self, group_name: str) -> None:
        try:
            self.client.xgroup_create(
                name=self.stream_name,
                groupname=group_name,
                id="0-0",
                mkstream=True,
            )

            logger.info(
                "Created Redis consumer group: %s",
                group_name,
            )

        except ResponseError as exc:
            if "BUSYGROUP" in str(exc):
                logger.info(
                    "Redis consumer group already exists: %s",
                    group_name,
                )
                return

            logger.exception(
                "Failed to create Redis consumer group: %s",
                group_name,
            )
            raise


    # ---- PRODUCER ----
    def publish(self, data: Dict) -> str:
        """Publish an event to Redis stream"""
        message_id = self.client.xadd(self.stream_name, data)
        logger.info("Published Redis event: stream=%s, message_id=%s",self.stream_name,message_id,)
        return message_id

    # ---- CONSUMER ----
    def listen(
        self,
        group_name: str,
        consumer_name: str,
        block_ms: int = 5000,
    ):
        events = self.client.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={self.stream_name: ">"},
            count=1,
            block=block_ms,
        )

        if not events:
            logger.debug("No events received from Redis stream: %s", self.stream_name)
            return None

        _, messages = events[0]
        message_id, data = messages[0]

        return {
            "id": message_id,
            "data": data,
        }


    def acknowledge(self, group_name: str, message_id: str) -> int:

        # Acknowledge the message in the Redis stream
        logger.info(
            "Acknowledging Redis event: stream=%s, group=%s, message_id=%s",
            self.stream_name,
            group_name,
            message_id,
        )

        return self.client.xack(
            self.stream_name,
            group_name,
            message_id,
        )

    def claim_pending(
    self,
    group_name: str,
    consumer_name: str,
    min_idle_time_ms: int = 300_000,
    start_id: str = "0-0",
    count: int = 10,
    ):
        result = self.client.xautoclaim(
            name=self.stream_name,
            groupname=group_name,
            consumername=consumer_name,
            min_idle_time=min_idle_time_ms,
            start_id=start_id,
            count=count,
        )


        logger.info(
            "XAUTOCLAIM requested_count=%d, actual_count=%d",
            count,
            len(messages),
        )

        next_cursor, messages = result[0], result[1]

        return next_cursor, [
            {"id": message_id, "data": data}
            for message_id, data in messages
        ]

redis_client = RedisStreamClient(stream_name="video_events")

import os
import redis
import json
from typing import Dict, Optional


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


    # ---- PRODUCER ----
    def publish(self, data: Dict) -> str:
        """Publish an event to Redis stream"""
        message_id = self.client.xadd(self.stream_name, data)
        print(f"[RedisStream] Published event: {message_id} -> {data}")
        return message_id

    # ---- CONSUMER ----
    def listen(self, block_ms: int = 5000) -> Optional[Dict]:
        """Listen for new events (simple non-group consumer)"""
        events = self.client.xread({self.stream_name: "$"}, block=block_ms, count=1)
        if not events:
            return None

        # Redis returns [(stream, [(id, {key: value})])]
        _, messages = events[0]
        message_id, data = messages[0]
        return {"id": message_id, "data": data}

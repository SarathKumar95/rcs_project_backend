import redis
import json
from typing import Dict, Optional


class RedisStreamClient:
    def __init__(self, host="localhost", port=6379, stream_name="video_events"):
        self.stream_name = stream_name
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

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

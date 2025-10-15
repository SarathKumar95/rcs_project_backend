from core.logger import get_logger
import os
import docker
from core.redis_stream import RedisStreamClient


logger = get_logger("video_transcoding")

def transcode_video(video_id: str, file_path: str):
    redis_client = RedisStreamClient()
    docker_client = docker.from_env()

    logger.info(f"[{video_id}] Starting transcoding for {file_path}")

    output_dir = f"/app/hls/{video_id}"
    os.makedirs(output_dir, exist_ok=True)

    ffmpeg_cmd = (
        f"ffmpeg -y -i /data/{file_path} "
        "-profile:v baseline -level 3.0 -start_number 0 "
        "-hls_time 10 -hls_list_size 0 -f hls /data/hls/"
        f"{video_id}/master.m3u8"
    )

    logger.info(f"[{video_id}] Running command: {ffmpeg_cmd}")

    container = docker_client.containers.run(
        image="linuxserver/ffmpeg",
        command=ffmpeg_cmd,
        volumes={
            "/absolute/host/videos": {"bind": "/data", "mode": "rw"}
        },
        detach=True,
        remove=True
    )

    logger.info(f"[{video_id}] Spawned FFmpeg container: {container.short_id}")

    for line in container.logs(stream=True):
        logger.info(f"[{video_id}] {line.decode().strip()}")

    result = container.wait()
    status = result.get("StatusCode")

    if status == 0:
        hls_path = f"videos/hls/{video_id}/master.m3u8"
        logger.info(f"[{video_id}]  Transcoding complete. Output: {hls_path}")
        redis_client.publish({
            "event": "video_transcoded",
            "data": {"video_id": video_id, "hls_path": hls_path}
        })
        logger.info(f"[{video_id}]  Published 'video_transcoded' event.")
    else:
        logger.error(f"[{video_id}]  Transcoding failed. Exit code: {status}")

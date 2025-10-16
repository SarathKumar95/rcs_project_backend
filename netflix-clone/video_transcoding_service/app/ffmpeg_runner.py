import os
import subprocess
import docker
import boto3
import requests

from core.redis_stream import RedisStreamClient
from core.logger import get_logger



logger = get_logger("video_transcoding")


MINIO_INTERNAL_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_URL")
BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME")

# log the bucket name
logger.info(f"Using MinIO bucket: {BUCKET_NAME}")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_PUBLIC_ENDPOINT,
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION"),
    config=boto3.session.Config(signature_version="s3v4"),
)

internal_s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_INTERNAL_ENDPOINT,  # ← minio:9000
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION"),
    config=boto3.session.Config(signature_version="s3v4"),
)

def transcode_video(video_id: str, file_key: str):
    """
    Downloads a video from MinIO (internal_s3), transcodes to HLS using FFmpeg,
    uploads the HLS output back to MinIO, and calls the video_upload_service internal API
    to notify that transcoding is complete.
    """

    try:
        logger.info(f"[{video_id}] 🎬 Starting transcoding for: {file_key}")

        # Step 1️: Prepare local temp directories
        local_video_path = f"/tmp/{os.path.basename(file_key)}"
        output_dir = f"/tmp/hls/{video_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Step 2️: Download the source video from MinIO
        logger.info(f"[{video_id}] ⬇️ Downloading {file_key} from {BUCKET_NAME} ...")
        internal_s3.download_file(BUCKET_NAME, file_key, local_video_path)
        logger.info(f"[{video_id}]  Download complete: {local_video_path}")

        # Step 3️: Run FFmpeg transcoding to HLS
        output_master = os.path.join(output_dir, "master.m3u8")

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", local_video_path,
            "-profile:v", "baseline",
            "-level", "3.0",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-f", "hls",
            output_master
        ]

        logger.info(f"[{video_id}] Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"[{video_id}] FFmpeg failed:\n{result.stderr}")
            return

        logger.info(f"[{video_id}]  Transcoding complete. Uploading HLS files...")

        # Step 4️: Upload generated HLS files back to MinIO
        for root, _, files in os.walk(output_dir):
            for f in files:
                local_path = os.path.join(root, f)
                s3_key = f"hls/{video_id}/{f}"

                internal_s3.upload_file(
                    local_path,
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={
                        "ContentType": "application/vnd.apple.mpegurl"
                        if f.endswith(".m3u8")
                        else "video/MP2T"
                    }
                )
                logger.info(f"[{video_id}] Uploaded {s3_key}")

        # Step 5️: Publish Redis event after successful transcoding
        # hls_path = f"hls/{video_id}/master.m3u8"
        # redis_client.publish({
        #     "event": "video_transcoded",
        #     "video_id": video_id,
        #     "hls_path": hls_path,
        #     "status": "transcoded"
        # })
        # logger.info(f"[{video_id}] Published 'video_transcoded' event for {hls_path}")

        # Step 5️⃣: Notify video_upload_service via internal API
        hls_path = f"hls/{video_id}/master.m3u8"
        notify_upload_service(video_id, hls_path)
        logger.info(f"[{video_id}] Notified upload service of transcoding completion.")

        # Step 6️: Cleanup
        try:
            os.remove(local_video_path)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[{video_id}] Transcoding failed: {e}")






def notify_upload_service(video_id: str, hls_path: str):
    """
    Notifies the video_upload_service that transcoding is complete
    via an internal API call. Requires INTERNAL_API_KEY in env.
    """

    upload_service_url = os.getenv(
        "VIDEO_UPLOAD_INTERNAL_URL",
        "http://video_upload:8002/videos/internal/post-transcode-update"
    )
    internal_api_key = os.getenv("INTERNAL_API_KEY")

    if not internal_api_key:
        logger.error("INTERNAL_API_KEY not found in environment!")
        return

    payload = {
        "video_id": video_id,
        "hls_path": hls_path,
        "upload_status" : 2
    }

    headers = {
        "x-internal-api-key": internal_api_key,
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"[{video_id}] Notifying upload service at {upload_service_url} ...")
        response = requests.post(upload_service_url, json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            logger.info(f"[{video_id}] Upload service response: {data.get('message', 'Success')}")
        else:
            logger.error(f"[{video_id}] Upload service failed [{response.status_code}]: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"[{video_id}] Internal API call failed: {e}")



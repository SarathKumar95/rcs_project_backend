import json
import os
import shutil
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



# Rendition settings: height, video bitrate, max bitrate, buffer size
RENDITIONS = [
    {"height": 360, "bitrate": "800k", "maxrate": "900k", "bufsize": "1200k"},
    {"height": 720, "bitrate": "2500k", "maxrate": "2800k", "bufsize": "3750k"},
    {"height": 1080, "bitrate": "5000k", "maxrate": "5500k", "bufsize": "7500k"},
]

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



def inspect_video(video_path: str) -> dict:
    """Read source dimensions and determine whether audio exists."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height",
            "-of", "json",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    streams = json.loads(result.stdout).get("streams", [])
    video_stream = next(
        (s for s in streams if s["codec_type"] == "video"),
        None,
    )

    if not video_stream:
        raise ValueError("Input file contains no video stream")

    return {
        "width": video_stream["width"],
        "height": video_stream["height"],
        "has_audio": any(s["codec_type"] == "audio" for s in streams),
    }


def transcode_to_hls(input_path: str, output_dir: str) -> None:
    """Generate adaptive-bitrate HLS renditions and a master playlist."""
    source = inspect_video(input_path)
    source_height = source["height"]
    source_width = source["width"]

    # Never upscale to a resolution larger than the source.
    renditions = [
        r for r in RENDITIONS
        if r["height"] <= source_height
    ]

    # For sources smaller than 360p, retain their approximate dimensions.
    if not renditions:
        target_height = source_height - (source_height % 2)
        target_width = int(source_width * target_height / source_height)
        target_width -= target_width % 2

        renditions = [{
            "height": target_height,
            "width": target_width,
            "bitrate": "500k",
            "maxrate": "600k",
            "bufsize": "750k",
        }]

    filters = []
    maps = []
    variant_entries = []

    for index, rendition in enumerate(renditions):
        height = rendition["height"]
        width = rendition.get("width")

        # Scale proportionally, preserving aspect ratio and even dimensions.
        if width is None:
            scale = (
                f"scale=w='trunc(iw*min(1\\,{height}/ih)/2)*2':"
                f"h='trunc(ih*min(1\\,{height}/ih)/2)*2'"
            )
        else:
            scale = f"scale={width}:{height}"

        filters.append(f"[0:v:0]{scale}[v{index}]")
        maps.extend(["-map", f"[v{index}]"])

        if source["has_audio"]:
            maps.extend(["-map", "0:a:0"])

        name = f"{height}p"
        variant_entries.append(
            f"v:{index},a:{index},name:{name}"
            if source["has_audio"]
            else f"v:{index},name:{name}"
        )

        os.makedirs(os.path.join(output_dir, name), exist_ok=True)

    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", ";".join(filters),
        *maps,
        "-c:v", "libx264",
        "-preset", "fast",
        "-profile:v", "main",
        "-pix_fmt", "yuv420p",
        "-sc_threshold", "0",
    ]

    for index, rendition in enumerate(renditions):
        command.extend([
            f"-b:v:{index}", rendition["bitrate"],
            f"-maxrate:v:{index}", rendition["maxrate"],
            f"-bufsize:v:{index}", rendition["bufsize"],
        ])

    if source["has_audio"]:
        command.extend([
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
            "-ar", "48000",
        ])

    command.extend([
        "-f", "hls",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename",
        os.path.join(output_dir, "%v", "segment_%05d.ts"),
        "-master_pl_name", "master.m3u8",
        "-var_stream_map", " ".join(variant_entries),
        os.path.join(output_dir, "%v", "index.m3u8"),
    ])

    logger.info(
        f"Source: {source_width}x{source_height}; "
        f"renditions: {[r['height'] for r in renditions]}"
    )

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed:\n{result.stderr}")




def transcode_video(video_id: str, file_key: str):
    """
    Downloads a video from MinIO (internal_s3), transcodes to HLS using FFmpeg,
    uploads the HLS output back to MinIO, and calls the video_upload_service internal API
    to notify that transcoding is complete.
    """

    # Step 1️: Prepare local temp directories
    local_video_path = f"/tmp/{os.path.basename(file_key)}"
    output_dir = f"/tmp/hls/{video_id}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        logger.info(f"[{video_id}] Starting transcoding for: {file_key}")



        # Step 2️: Download the source video from MinIO
        logger.info(f"[{video_id}] Downloading {file_key} from {BUCKET_NAME} ...")
        internal_s3.download_file(BUCKET_NAME, file_key, local_video_path)
        logger.info(f"[{video_id}]  Download complete: {local_video_path}")

        # # Step 3️: Run FFmpeg transcoding to HLS
        # output_master = os.path.join(output_dir, "master.m3u8")

        # Step 3: Generate multiple HLS resolutions and master playlist
        # This function contains the FFmpeg configuration.
        transcode_to_hls(local_video_path, output_dir)

        logger.info(f"[{video_id}] HLS generation complete. Uploading files...")


        # ffmpeg_cmd = [
        #     "ffmpeg", "-y",
        #     "-i", local_video_path,
        #     "-profile:v", "baseline",
        #     "-level", "3.0",
        #     "-start_number", "0",
        #     "-hls_time", "10",
        #     "-hls_list_size", "0",
        #     "-f", "hls",
        #     output_master
        # ]

        # logger.info(f"[{video_id}] Running FFmpeg: {' '.join(ffmpeg_cmd)}")
        # result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        # if result.returncode != 0:
        #     logger.error(f"[{video_id}] FFmpeg failed:\n{result.stderr}")
        #     return

        # logger.info(f"[{video_id}]  Transcoding complete. Uploading HLS files...")

        # Step 4: Upload all generated playlists and segments
        for root, _, files in os.walk(output_dir):
            for filename in files:
                local_path = os.path.join(root, filename)

                # Preserve subdirectories such as 360p/, 720p/, and 1080p/
                relative_path = os.path.relpath(local_path, output_dir)
                relative_path = relative_path.replace(os.sep, "/")

                s3_key = f"hls/{video_id}/{relative_path}"

                content_type = (
                    "application/vnd.apple.mpegurl"
                    if filename.endswith(".m3u8")
                    else "video/MP2T"
                )

                internal_s3.upload_file(
                    local_path,
                    BUCKET_NAME,
                    s3_key,
                    ExtraArgs={"ContentType": content_type},
                )

                logger.info(f"[{video_id}] Uploaded {s3_key}")


        # Step 5: Notify only after every file has uploaded successfully
        hls_path = f"hls/{video_id}/master.m3u8"

        notify_upload_service(video_id, hls_path)

        logger.info(f"[{video_id}] Notified upload service")

    except Exception:
        logger.exception(f"[{video_id}] Transcoding failed")
        raise

    finally:
        if os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
            except OSError:
                logger.exception(
                    f"[{video_id}] Failed to remove source file: "
                    f"{local_video_path}"
                )

        if os.path.exists(output_dir):
            try:
                shutil.rmtree(output_dir)
            except OSError:
                logger.exception(
                    f"[{video_id}] Failed to clean HLS directory: "
                    f"{output_dir}"
                )






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



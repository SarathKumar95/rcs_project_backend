"""Helpers for retrieving HLS assets from MinIO."""

import posixpath
from pathlib import PurePosixPath

from botocore.exceptions import ClientError

from app.deps.s3_client import BUCKET_NAME, internal_s3


def get_hls_object(master_playlist_path: str, requested_path: str):
    """
    Retrieve one HLS asset belonging to a video's master playlist.

    `master_playlist_path` is the exact key saved after transcoding, for
    example: hls/<video-id>/master.m3u8.
    `requested_path` is the path requested by the HLS player, for example:
    master.m3u8, 720p/index.m3u8, or 720p/segment_00001.ts.
    """
    if not BUCKET_NAME:
        raise RuntimeError("MINIO_BUCKET_NAME is not configured")

    requested = PurePosixPath(requested_path)
    if (
        not requested_path
        or requested.is_absolute()
        or any(part in ("", ".", "..") for part in requested.parts)
        or "\\\\" in requested_path
    ):
        raise ValueError("Invalid HLS file path")

    playlist_key = PurePosixPath(master_playlist_path)
    if playlist_key.is_absolute() or ".." in playlist_key.parts:
        raise ValueError("Invalid stored HLS playlist path")

    hls_directory = str(playlist_key.parent)
    object_key = posixpath.join(hls_directory, requested.as_posix())

    try:
        return internal_s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in {"NoSuchKey", "404", "NotFound"}:
            raise FileNotFoundError(object_key) from exc
        raise

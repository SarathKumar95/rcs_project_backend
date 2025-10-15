# ---------------------------------------------------------
# Video Transcoding Worker
# Lightweight, production-safe, Python build
# ---------------------------------------------------------
FROM python:3.10-alpine

# Base working directory
WORKDIR /app/app

# Install system dependencies (for ffmpeg + Redis + logging libs)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    ffmpeg

# Copy requirements first for caching
COPY ./video_transcoding_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy shared core utilities
COPY ./core /app/core

# Copy the service's app code
COPY ./video_transcoding_service/app /app/app

# Ensure logs directory exists
RUN mkdir -p /app/logs

# Add Python path
ENV PYTHONPATH=/app

# Run the worker
CMD ["python", "worker.py"]

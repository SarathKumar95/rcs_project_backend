# Start from a base Python image
FROM python:3.9-slim

# Set work directory
WORKDIR /app/video_upload_service

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl gcc libpq-dev build-essential && \
    apt-get clean

# Copy dependency file and install
COPY video_upload_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the service and shared project code
COPY video_upload_service/app ./app
COPY core /app/core

ENV PYTHONPATH=/app

# Set environment variables (if needed)
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

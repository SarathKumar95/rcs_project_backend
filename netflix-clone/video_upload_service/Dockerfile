# Start from a base Python image
FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl gcc libpq-dev build-essential && \
    apt-get clean

# Copy dependency file and install
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app
COPY ./app ./app

# Set environment variables (if needed)
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

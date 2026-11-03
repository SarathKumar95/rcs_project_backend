# Start from a base Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY user_service/requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service and shared project code
COPY user_service/ /app/
COPY core/ /app/core/

ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Command to run the application (example for FastAPI)
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

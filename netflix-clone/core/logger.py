import logging
import sys
import os

def get_logger(service_name: str = "netflix_clone") -> logging.Logger:
    """
    Creates a logger for a specific service.
    Example: get_logger("video_transcoding") → logs/video_transcoding.log
    """

    # Log directory
    LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
    os.makedirs(LOG_DIR, exist_ok=True)

    # Log file name per service
    log_file_path = os.path.join(LOG_DIR, f"{service_name}.log")

    # Create or fetch logger
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not logger.handlers:
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler (per-service log)
        file_handler = logging.FileHandler(log_file_path)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

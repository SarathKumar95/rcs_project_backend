import logging
import sys

logger = logging.getLogger("netflix_clone")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

if not logger.handlers:  # prevent duplicate logs
    logger.addHandler(handler)

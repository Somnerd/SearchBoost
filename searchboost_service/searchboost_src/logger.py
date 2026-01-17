import sys
import logging

def setup_logger(level_str="info"):
    # Convert string to logging constant
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    # Fallback to INFO if the user types something weird
    level = levels.get(level_str.lower(), logging.INFO)

    logger = logging.getLogger("SearchBoost")

    # Only configure if it doesn't have handlers (prevents double logging)
    if not logger.handlers:
        logger.setLevel(level)

        # Explicitly use sys.stdout to ensure logs go to the standard output
        # In Docker, sys.stdout/stderr are usually the targets for 'docker logs'
        handler = logging.StreamHandler(sys.stdout)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Allow updating the level even if handlers exist
    logger.setLevel(level)

    # This is the crucial part for Docker:
    # Force flushing of the stream if you suspect buffering is still happening
    # Note: Setting the environment variable PYTHONUNBUFFERED=1 is still the 'best' way
    return logger
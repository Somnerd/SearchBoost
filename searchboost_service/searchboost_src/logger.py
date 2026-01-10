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
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Allow updating the level even if handlers exist
    logger.setLevel(level)

    return logger
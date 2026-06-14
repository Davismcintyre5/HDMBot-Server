"""
server/utils/logger.py — Logging configuration
"""
import os
import logging
import logging.handlers
from datetime import datetime
from config.settings import settings


def setup_logger(name: str = "hdm_bot") -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Ensure log directory exists
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    
    # Set level
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.DEBUG)
    logger.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler (daily rotation)
    log_file = os.path.join(settings.LOG_DIR, f"bot_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=settings.LOG_RETENTION_DAYS,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# Default logger instance
logger = setup_logger()
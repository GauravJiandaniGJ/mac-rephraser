"""Logging configuration for Rephrase app."""

import logging
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".config" / "rephrase" / "logs"


def setup_logger() -> logging.Logger:
    """Setup and return the app logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Log file with date
    log_file = LOG_DIR / f"rephrase_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    logger = logging.getLogger("rephrase")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler (for when running in terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter("%(levelname)-7s | %(message)s")
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
log = setup_logger()

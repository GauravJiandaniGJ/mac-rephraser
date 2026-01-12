"""Logging configuration for Rephrase app."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def get_log_directory() -> Path:
    """Get platform-specific log directory."""
    if sys.platform == "darwin":
        # macOS: ~/Library/Logs/Rephrase/
        return Path.home() / "Library" / "Logs" / "Rephrase"
    elif sys.platform == "win32":
        # Windows: %LOCALAPPDATA%/Rephrase/logs/
        local_app_data = Path.home() / "AppData" / "Local"
        return local_app_data / "Rephrase" / "logs"
    else:
        # Linux/other: ~/.config/rephrase/logs/ (XDG standard)
        return Path.home() / ".config" / "rephrase" / "logs"


LOG_DIR = get_log_directory()


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

"""
Tests for logger.py - logging configuration.
"""

import pytest
from pathlib import Path


class TestLogger:
    """Tests for logger.py - logging configuration"""

    def test_logger_is_configured(self):
        """Logger should be properly configured"""
        from logger import log

        assert log is not None
        assert log.name == "rephrase"

    def test_log_directory_constant(self):
        """LOG_DIR should point to correct location"""
        from logger import LOG_DIR

        expected = Path.home() / ".config" / "rephrase" / "logs"
        assert LOG_DIR == expected

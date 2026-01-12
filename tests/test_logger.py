"""
Tests for logger.py - logging configuration.
"""

import sys
from pathlib import Path


class TestLogger:
    """Tests for logger.py - logging configuration"""

    def test_logger_is_configured(self):
        """Logger should be properly configured"""
        from logger import log

        assert log is not None
        assert log.name == "rephrase"

    def test_log_directory_platform_specific(self):
        """LOG_DIR should point to platform-specific location"""
        from logger import LOG_DIR

        if sys.platform == "darwin":
            expected = Path.home() / "Library" / "Logs" / "Rephrase"
        elif sys.platform == "win32":
            expected = Path.home() / "AppData" / "Local" / "Rephrase" / "logs"
        else:
            expected = Path.home() / ".config" / "rephrase" / "logs"

        assert LOG_DIR == expected

    def test_get_log_directory_function(self):
        """get_log_directory should return a Path"""
        from logger import get_log_directory

        result = get_log_directory()
        assert isinstance(result, Path)
        assert "Rephrase" in str(result) or "rephrase" in str(result)

"""Usage statistics tracking for Rephrase app."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from logger import log

STATS_DIR = Path.home() / ".config" / "rephrase"
STATS_FILE = STATS_DIR / "usage_stats.json"
RETENTION_DAYS = 30


def _ensure_stats_dir():
    """Create stats directory if it doesn't exist."""
    STATS_DIR.mkdir(parents=True, exist_ok=True)


def _load_stats() -> dict:
    """Load usage stats from file."""
    _ensure_stats_dir()
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_stats(stats: dict) -> None:
    """Save usage stats to file."""
    _ensure_stats_dir()
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def _cleanup_old_entries(stats: dict) -> dict:
    """Remove entries older than RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    cleaned = {date: count for date, count in stats.items() if date >= cutoff_str}
    return cleaned


def record_rephrase() -> None:
    """Record a rephrase operation for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    stats = _load_stats()

    # Increment today's count
    stats[today] = stats.get(today, 0) + 1

    # Cleanup old entries
    stats = _cleanup_old_entries(stats)

    _save_stats(stats)
    log.debug(f"Recorded rephrase. Today's count: {stats[today]}")


def get_today_count() -> int:
    """Get the number of rephrases today."""
    today = datetime.now().strftime("%Y-%m-%d")
    stats = _load_stats()
    return stats.get(today, 0)


def get_total_count() -> int:
    """Get total rephrases in the last 30 days."""
    stats = _load_stats()
    stats = _cleanup_old_entries(stats)
    return sum(stats.values())


def get_stats_summary() -> dict:
    """Get a summary of usage statistics."""
    stats = _load_stats()
    stats = _cleanup_old_entries(stats)

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = stats.get(today, 0)
    total_count = sum(stats.values())
    days_with_usage = len(stats)

    return {
        "today": today_count,
        "total_30_days": total_count,
        "days_active": days_with_usage,
    }

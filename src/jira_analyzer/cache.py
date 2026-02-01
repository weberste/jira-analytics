"""Local caching for JIRA API responses."""

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path


CACHE_DIR = Path.home() / ".jira-analyzer" / "cache"
CACHE_TTL_HOURS = 24


def _get_cache_key(jql: str, start_date: date, end_date: date) -> str:
    """Generate cache key from query parameters."""
    key_str = f"{jql}|{start_date.isoformat()}|{end_date.isoformat()}"
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]


def _get_cache_path(cache_key: str) -> Path:
    """Get path to cache file."""
    return CACHE_DIR / f"{cache_key}.json"


def get_cached_issues(
    jql: str, start_date: date, end_date: date
) -> list[dict] | None:
    """Retrieve cached issues if available and not expired.

    Args:
        jql: JQL query string
        start_date: Analysis start date
        end_date: Analysis end date

    Returns:
        List of cached issue dicts, or None if cache miss/expired
    """
    cache_key = _get_cache_key(jql, start_date, end_date)
    cache_path = _get_cache_path(cache_key)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path, "r") as f:
            data = json.load(f)

        # Check expiration
        cached_at = datetime.fromisoformat(data["cached_at"])
        if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            return None

        return data["issues"]

    except (json.JSONDecodeError, KeyError, ValueError):
        # Corrupted cache file
        return None


def save_to_cache(
    jql: str, start_date: date, end_date: date, issues: list[dict]
) -> None:
    """Save issues to cache.

    Args:
        jql: JQL query string
        start_date: Analysis start date
        end_date: Analysis end date
        issues: List of issue dicts to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_key = _get_cache_key(jql, start_date, end_date)
    cache_path = _get_cache_path(cache_key)

    data = {
        "jql": jql,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "cached_at": datetime.now().isoformat(),
        "issues": issues,
    }

    with open(cache_path, "w") as f:
        json.dump(data, f)

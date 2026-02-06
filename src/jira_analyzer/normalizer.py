"""Normalize raw time entries to max hours per developer per day."""

from collections import defaultdict
from datetime import date

from jira_analyzer.config import DEFAULT_MAX_NORMALIZED_HOURS
from jira_analyzer.models import Issue, NormalizedTimeEntry, RawTimeEntry


def normalize_time_entries(
    raw_entries: list[RawTimeEntry],
    issues: list[Issue],
    max_normalized_hours: float = DEFAULT_MAX_NORMALIZED_HOURS,
) -> list[NormalizedTimeEntry]:
    """Normalize raw time entries to max hours per developer per day.

    For each developer on each day:
    - Sum their raw hours across all issues
    - If total > max_normalized_hours, scale DOWN proportionally
    - If total <= max_normalized_hours, keep raw hours (no scale-up)

    Args:
        raw_entries: List of raw time entries (assigned only, not unassigned)
        issues: List of issues for enriching output with titles/types
        max_normalized_hours: Maximum hours per developer per day (default: 7.0)

    Returns:
        List of normalized time entries
    """
    # Build issue lookup for enrichment
    issue_lookup = {issue.key: issue for issue in issues}

    # Group entries by (developer, date)
    by_dev_date: dict[tuple[str, date], list[RawTimeEntry]] = defaultdict(list)
    for entry in raw_entries:
        key = (entry.developer, entry.date)
        by_dev_date[key].append(entry)

    normalized: list[NormalizedTimeEntry] = []

    for (developer, day), entries in by_dev_date.items():
        # Calculate total raw hours for this developer on this day
        total_raw = sum(e.raw_hours for e in entries)

        if total_raw <= 0:
            continue

        # Only scale down if exceeds max, never scale up
        if total_raw > max_normalized_hours:
            scale_factor = max_normalized_hours / total_raw
        else:
            scale_factor = 1.0  # Keep raw hours

        for entry in entries:
            issue = issue_lookup.get(entry.issue_key)
            if not issue:
                continue

            normalized_hours = entry.raw_hours * scale_factor

            normalized.append(
                NormalizedTimeEntry(
                    issue_key=entry.issue_key,
                    issue_title=issue.title,
                    issue_type=issue.issue_type,
                    epic_key=issue.epic_key,
                    epic_title=issue.epic_title,
                    developer=developer,
                    date=day,
                    raw_hours=round(entry.raw_hours, 2),
                    normalized_hours=round(normalized_hours, 2),
                )
            )

    # Sort by date, then developer, then issue
    normalized.sort(key=lambda e: (e.date, e.developer, e.issue_key))

    return normalized

"""Normalize raw time entries to 8-hour workdays per developer."""

from collections import defaultdict
from datetime import date

from jira_analyzer.models import Issue, NormalizedTimeEntry, RawTimeEntry


MAX_NORMALIZED_HOURS = 7.0  # Assume no one works at 100% capacity


def normalize_time_entries(
    raw_entries: list[RawTimeEntry],
    issues: list[Issue],
) -> list[NormalizedTimeEntry]:
    """Normalize raw time entries to max 7 hours per developer per day.

    For each developer on each day:
    - Sum their raw hours across all issues
    - If total > 7 hours, scale DOWN proportionally to 7 hours
    - If total <= 7 hours, keep raw hours (no scale-up)

    Args:
        raw_entries: List of raw time entries (assigned only, not unassigned)
        issues: List of issues for enriching output with titles/types

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
        if total_raw > MAX_NORMALIZED_HOURS:
            scale_factor = MAX_NORMALIZED_HOURS / total_raw
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


def aggregate_by_issue(entries: list[NormalizedTimeEntry]) -> list[NormalizedTimeEntry]:
    """Aggregate normalized entries by issue (sum across dates).

    Useful for summary views that don't need day-by-day breakdown.
    """
    # Group by (issue_key, developer)
    by_issue_dev: dict[tuple[str, str], list[NormalizedTimeEntry]] = defaultdict(list)
    for entry in entries:
        key = (entry.issue_key, entry.developer)
        by_issue_dev[key].append(entry)

    aggregated: list[NormalizedTimeEntry] = []

    for (issue_key, developer), group in by_issue_dev.items():
        # Use first entry as template
        template = group[0]
        total_raw = sum(e.raw_hours for e in group)
        total_normalized = sum(e.normalized_hours for e in group)

        aggregated.append(
            NormalizedTimeEntry(
                issue_key=issue_key,
                issue_title=template.issue_title,
                issue_type=template.issue_type,
                epic_key=template.epic_key,
                epic_title=template.epic_title,
                developer=developer,
                date=min(e.date for e in group),  # Use earliest date
                raw_hours=round(total_raw, 2),
                normalized_hours=round(total_normalized, 2),
            )
        )

    # Sort by issue key, then developer
    aggregated.sort(key=lambda e: (e.issue_key, e.developer))

    return aggregated

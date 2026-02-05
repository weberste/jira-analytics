"""Time calculation from JIRA status history."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR

from jira_analyzer.models import AssigneeChange, Issue, RawTimeEntry, StatusTransition


# Default workday boundaries (used when no config provided)
DEFAULT_WORKDAY_START = time(8, 0)  # 8:00 AM
DEFAULT_WORKDAY_END = time(16, 0)  # 4:00 PM


@dataclass
class WorkdayConfig:
    """Configuration for workday boundaries."""

    start: time = DEFAULT_WORKDAY_START
    end: time = DEFAULT_WORKDAY_END

    @property
    def hours(self) -> float:
        """Compute workday duration in hours."""
        start_minutes = self.start.hour * 60 + self.start.minute
        end_minutes = self.end.hour * 60 + self.end.minute
        return (end_minutes - start_minutes) / 60.0


@dataclass
class ActivePeriod:
    """A period when an issue was in an active status."""

    start: datetime
    end: datetime
    developer: str | None


def is_weekend(d: date) -> bool:
    """Check if a date is a weekend (Saturday or Sunday)."""
    return d.weekday() >= 5


def get_workdays_in_range(start_date: date, end_date: date) -> list[date]:
    """Get all workdays (Mon-Fri) between start and end dates, inclusive."""
    if start_date > end_date:
        return []

    # Generate all weekdays in range
    return list(
        rrule(
            DAILY,
            dtstart=start_date,
            until=end_date,
            byweekday=(MO, TU, WE, TH, FR),
        )
    )


def clip_to_workday(
    dt: datetime,
    workday_date: date,
    workday_config: WorkdayConfig | None = None,
) -> datetime:
    """Clip a datetime to workday boundaries for a given date."""
    if workday_config is None:
        workday_config = WorkdayConfig()

    day_start = datetime.combine(workday_date, workday_config.start)
    day_end = datetime.combine(workday_date, workday_config.end)

    # Make timezone-naive for comparison if needed
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    if dt < day_start:
        return day_start
    if dt > day_end:
        return day_end
    return dt


def calculate_hours_for_day(
    period_start: datetime,
    period_end: datetime,
    workday_date: date,
    workday_config: WorkdayConfig | None = None,
) -> float:
    """Calculate hours worked on a specific workday within an active period.

    Args:
        period_start: When the active period started
        period_end: When the active period ended
        workday_date: The specific workday to calculate hours for
        workday_config: Workday boundaries configuration

    Returns:
        Hours worked (0 to workday duration)
    """
    if workday_config is None:
        workday_config = WorkdayConfig()

    day_start = datetime.combine(workday_date, workday_config.start)
    day_end = datetime.combine(workday_date, workday_config.end)

    # Make timezone-naive for comparison
    if period_start.tzinfo is not None:
        period_start = period_start.replace(tzinfo=None)
    if period_end.tzinfo is not None:
        period_end = period_end.replace(tzinfo=None)

    # Check if period overlaps with this workday
    if period_end <= day_start or period_start >= day_end:
        return 0.0

    # Clip period to workday boundaries
    effective_start = max(period_start, day_start)
    effective_end = min(period_end, day_end)

    # Calculate hours
    duration = effective_end - effective_start
    hours = duration.total_seconds() / 3600

    # Clamp to valid range
    return max(0.0, min(workday_config.hours, hours))


def find_developer_at_time(
    timestamp: datetime,
    assignee_history: list[AssigneeChange],
    current_developer: str | None,
    current_assignee: str | None,
    developer_field: str | None,
) -> str | None:
    """Find who was the developer at a given timestamp.

    Priority order:
    1. Developer field value at that time (from history)
    2. Assignee at that time (from history)
    3. Current Developer field value
    4. Current Assignee value
    5. None (will be marked as Unassigned)
    """
    # Make timestamp naive for comparison
    if timestamp.tzinfo is not None:
        timestamp = timestamp.replace(tzinfo=None)

    # Track developer field changes
    developer_at_time = None
    assignee_at_time = None

    for change in assignee_history:
        change_time = change.timestamp
        if change_time.tzinfo is not None:
            change_time = change_time.replace(tzinfo=None)

        if change_time > timestamp:
            break

        if developer_field and change.field == developer_field:
            developer_at_time = change.to_value
        elif change.field.lower() == "assignee":
            assignee_at_time = change.to_value

    # Apply priority order
    if developer_at_time:
        return developer_at_time
    if assignee_at_time:
        return assignee_at_time
    if current_developer:
        return current_developer
    if current_assignee:
        return current_assignee

    return None


def find_active_periods(
    issue: Issue,
    active_statuses: list[str],
    developer_field: str | None,
) -> list[ActivePeriod]:
    """Find all periods when an issue was in an active status.

    Handles reassignments by splitting periods when assignee changes.
    """
    periods: list[ActivePeriod] = []

    # Sort transitions by timestamp
    transitions = sorted(issue.status_history, key=lambda t: t.timestamp)

    # Track when we enter/exit active status
    in_active_since: datetime | None = None

    for transition in transitions:
        entering_active = transition.to_status in active_statuses and not in_active_since
        leaving_active = transition.to_status not in active_statuses and in_active_since

        if entering_active:
            in_active_since = transition.timestamp
        elif leaving_active:
            # Find developer for this period
            developer = find_developer_at_time(
                in_active_since,
                issue.assignee_history,
                issue.current_developer,
                issue.current_assignee,
                developer_field,
            )

            # Check for reassignments during this period
            periods.extend(
                split_period_by_reassignments(
                    in_active_since,
                    transition.timestamp,
                    issue.assignee_history,
                    issue.current_developer,
                    issue.current_assignee,
                    developer_field,
                )
            )
            in_active_since = None

    # Handle case where issue is still in active status
    if in_active_since:
        # Use current time as end
        periods.extend(
            split_period_by_reassignments(
                in_active_since,
                datetime.now(),
                issue.assignee_history,
                issue.current_developer,
                issue.current_assignee,
                developer_field,
            )
        )

    return periods


def split_period_by_reassignments(
    period_start: datetime,
    period_end: datetime,
    assignee_history: list[AssigneeChange],
    current_developer: str | None,
    current_assignee: str | None,
    developer_field: str | None,
) -> list[ActivePeriod]:
    """Split an active period by any reassignments that occurred during it."""
    periods: list[ActivePeriod] = []

    # Make timestamps naive for comparison
    if period_start.tzinfo is not None:
        period_start = period_start.replace(tzinfo=None)
    if period_end.tzinfo is not None:
        period_end = period_end.replace(tzinfo=None)

    # Find all reassignments during this period
    reassignments = []
    for change in assignee_history:
        change_time = change.timestamp
        if change_time.tzinfo is not None:
            change_time = change_time.replace(tzinfo=None)

        if period_start < change_time < period_end:
            reassignments.append(change_time)

    # Add boundaries
    boundaries = [period_start] + sorted(set(reassignments)) + [period_end]

    # Create periods between boundaries
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]

        developer = find_developer_at_time(
            start,
            assignee_history,
            current_developer,
            current_assignee,
            developer_field,
        )

        periods.append(ActivePeriod(start=start, end=end, developer=developer))

    return periods


def calculate_raw_time(
    issues: list[Issue],
    active_statuses: list[str],
    start_date: date,
    end_date: date,
    developer_field: str | None = None,
    workday_start: time | None = None,
    workday_end: time | None = None,
) -> tuple[list[RawTimeEntry], list[RawTimeEntry]]:
    """Calculate raw time entries for all issues.

    Args:
        issues: List of issues to analyze
        active_statuses: Statuses that count as "active work"
        start_date: Start of analysis timeframe
        end_date: End of analysis timeframe
        developer_field: Custom field name for developer (optional)
        workday_start: Start of workday (default: 08:00)
        workday_end: End of workday (default: 16:00)

    Returns:
        Tuple of (assigned entries, unassigned entries)
    """
    assigned_entries: list[RawTimeEntry] = []
    unassigned_entries: list[RawTimeEntry] = []

    # Build workday config
    workday_config = WorkdayConfig(
        start=workday_start or DEFAULT_WORKDAY_START,
        end=workday_end or DEFAULT_WORKDAY_END,
    )

    # Get all workdays in the timeframe
    workdays = get_workdays_in_range(start_date, end_date)

    for issue in issues:
        # Find all active periods for this issue
        periods = find_active_periods(issue, active_statuses, developer_field)

        for period in periods:
            for workday in workdays:
                workday_date = workday.date() if isinstance(workday, datetime) else workday

                hours = calculate_hours_for_day(
                    period.start, period.end, workday_date, workday_config
                )

                if hours > 0:
                    is_unassigned = period.developer is None
                    entry = RawTimeEntry(
                        issue_key=issue.key,
                        developer=period.developer or "Unassigned",
                        date=workday_date,
                        raw_hours=hours,
                        is_unassigned=is_unassigned,
                    )

                    if is_unassigned:
                        unassigned_entries.append(entry)
                    else:
                        assigned_entries.append(entry)

    return assigned_entries, unassigned_entries

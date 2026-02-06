"""Analysis orchestration for web interface - bridges web layer to core modules."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

from jira_analyzer.cache import get_cached_issues, save_to_cache
from jira_analyzer.config import Config, config_exists, load_config
from jira_analyzer.jira_client import (
    AuthenticationError,
    JiraClient,
    RateLimitError,
    build_date_filtered_jql,
)
from jira_analyzer.models import NormalizedTimeEntry
from jira_analyzer.normalizer import normalize_time_entries
from jira_analyzer.time_calculator import calculate_raw_time


# Color palette for chart segments
CHART_COLORS = [
    "#4e79a7",  # Blue
    "#f28e2c",  # Orange
    "#e15759",  # Red
    "#76b7b2",  # Teal
    "#59a14f",  # Green
    "#edc949",  # Yellow
    "#af7aa1",  # Purple
    "#ff9da7",  # Pink
    "#9c755f",  # Brown
    "#bab0ab",  # Gray
    "#6b9ac4",  # Light Blue
    "#d4a6c8",  # Light Purple
]


@dataclass
class EpicChartData:
    """Data structure for rendering the epic allocation chart."""

    labels: list[str]
    values: list[float]
    percentages: list[float]
    colors: list[str]
    epic_keys: list[str | None]


@dataclass
class IssueRow:
    """Flattened row structure for the issue table."""

    issue_key: str
    issue_url: str
    issue_title: str
    issue_type: str
    epic_key: str | None
    epic_title: str | None
    raw_hours: float
    normalized_hours: float
    unassigned: bool = False


@dataclass
class WebAnalysisResult:
    """Extended analysis result with web-specific formatting."""

    jql_query: str
    raw_jql_query: str
    start_date: date
    end_date: date
    total_issues: int
    issues_with_time: int
    issues_with_no_time: int
    unassigned_issues: int
    entries: list[NormalizedTimeEntry]
    from_cache: bool
    jira_url: str
    epic_chart_data: EpicChartData
    issue_table_data: list[IssueRow]
    issues_no_time_data: list[IssueRow]


class AnalysisError(Exception):
    """Base exception for analysis errors."""

    pass


class ConfigNotFoundError(AnalysisError):
    """Configuration file not found."""

    pass


class InvalidConfigError(AnalysisError):
    """Configuration is invalid."""

    pass


class JiraAuthError(AnalysisError):
    """JIRA authentication failed."""

    pass


class JiraRateLimitError(AnalysisError):
    """JIRA rate limit exceeded."""

    pass


class InvalidJqlError(AnalysisError):
    """Invalid JQL query."""

    pass


class NoIssuesFoundError(AnalysisError):
    """No issues found matching query."""

    pass


class NoActivityFoundError(AnalysisError):
    """No work activity found in timeframe."""

    pass


def run_analysis(
    jql: str,
    from_date: date,
    to_date: date,
    no_cache: bool = False,
    track_epic_time: bool = False,
) -> WebAnalysisResult:
    """Run analysis and return web-formatted results.

    Args:
        jql: JQL query string
        from_date: Start of analysis period
        to_date: End of analysis period
        no_cache: If True, bypass cache
        track_epic_time: If True, include epic issues in time calculation

    Returns:
        WebAnalysisResult with chart and table data

    Raises:
        ConfigNotFoundError: If config file not found
        InvalidConfigError: If config is invalid
        JiraAuthError: If JIRA authentication fails
        JiraRateLimitError: If rate limited
        InvalidJqlError: If JQL is invalid
        NoIssuesFoundError: If no issues match query
        NoActivityFoundError: If no activity in timeframe
    """
    # Load configuration
    if not config_exists():
        raise ConfigNotFoundError(
            "Configuration not found. Run 'jira-analyzer config init' in your terminal to set up."
        )

    try:
        config = load_config()
    except ValueError as e:
        raise InvalidConfigError(
            f"Invalid configuration. Check your settings with 'jira-analyzer config show'. Error: {e}"
        )

    # Build the actual JQL with date filters
    raw_jql = build_date_filtered_jql(jql, from_date, to_date, track_epic_time)

    # Check cache first
    raw_issues = None
    from_cache_flag = False
    if not no_cache:
        raw_issues = get_cached_issues(raw_jql, from_date, to_date)
        if raw_issues is not None:
            from_cache_flag = True

    client = JiraClient(config)

    if raw_issues is not None:
        issues = [client._parse_issue(issue_dict) for issue_dict in raw_issues]
    else:
        # Fetch from JIRA
        try:
            raw_issues = client.search_all_issues(raw_jql)
        except AuthenticationError:
            raise JiraAuthError(
                "JIRA authentication failed. Check your credentials with 'jira-analyzer config show'."
            )
        except RateLimitError:
            raise JiraRateLimitError(
                "JIRA rate limit exceeded. Please wait a moment and try again."
            )
        except ValueError as e:
            raise InvalidJqlError(f"Invalid JQL query: {e}. Check your query syntax.")

        # Save to cache
        if raw_issues:
            save_to_cache(raw_jql, from_date, to_date, raw_issues)

        issues = [client._parse_issue(issue_dict) for issue_dict in raw_issues]

    if not issues:
        raise NoIssuesFoundError("No issues found matching your query.")

    # Calculate raw time
    assigned_entries, unassigned_entries = calculate_raw_time(
        issues=issues,
        active_statuses=config.active_statuses,
        start_date=from_date,
        end_date=to_date,
        developer_field=config.developer_field,
        workday_start=config.workday_start,
        workday_end=config.workday_end,
    )

    # Combine entries
    all_entries = assigned_entries.copy()
    for entry in unassigned_entries:
        entry.developer = "Unassigned"
        all_entries.append(entry)

    if not all_entries:
        raise NoActivityFoundError("No work activity found in the specified timeframe.")

    # Normalize
    normalized_entries = normalize_time_entries(
        all_entries, issues, max_normalized_hours=config.max_normalized_hours
    )

    # Build statistics
    total_issues = len(issues)
    all_issue_keys = {issue.key for issue in issues}
    issues_with_time_keys = {e.issue_key for e in all_entries}
    unassigned_issue_keys = {e.issue_key for e in unassigned_entries}
    issues_no_time_keys = all_issue_keys - issues_with_time_keys

    # Build chart data
    epic_chart_data = _build_epic_chart_data(normalized_entries)

    # Build issue table data
    issue_table_data = _build_issue_table_data(normalized_entries, config.jira_url)

    # Build issues without time data
    issues_no_time_data = _build_issues_no_time_data(
        issues, issues_no_time_keys, config.jira_url
    )

    return WebAnalysisResult(
        jql_query=jql,
        raw_jql_query=raw_jql,
        start_date=from_date,
        end_date=to_date,
        total_issues=total_issues,
        issues_with_time=len(issues_with_time_keys),
        issues_with_no_time=len(issues_no_time_keys),
        unassigned_issues=len(unassigned_issue_keys),
        entries=normalized_entries,
        from_cache=from_cache_flag,
        jira_url=config.jira_url,
        epic_chart_data=epic_chart_data,
        issue_table_data=issue_table_data,
        issues_no_time_data=issues_no_time_data,
    )


def _build_epic_chart_data(entries: list[NormalizedTimeEntry]) -> EpicChartData:
    """Build chart data from normalized entries."""
    # Aggregate by epic
    epic_hours: dict[tuple[str | None, str | None], float] = defaultdict(float)
    for entry in entries:
        key = (entry.epic_key, entry.epic_title)
        epic_hours[key] += entry.normalized_hours

    # Sort by hours descending
    sorted_epics = sorted(epic_hours.items(), key=lambda x: -x[1])

    # Calculate total
    total_hours = sum(epic_hours.values())

    # Build arrays
    labels = []
    values = []
    percentages = []
    colors = []
    epic_keys = []

    for i, ((epic_key, epic_title), hours) in enumerate(sorted_epics):
        labels.append(epic_title or "No Epic")
        values.append(round(hours, 1))
        percentages.append(round(100 * hours / total_hours, 1) if total_hours > 0 else 0)
        colors.append(CHART_COLORS[i % len(CHART_COLORS)])
        epic_keys.append(epic_key)

    return EpicChartData(
        labels=labels,
        values=values,
        percentages=percentages,
        colors=colors,
        epic_keys=epic_keys,
    )


def _build_issue_table_data(
    entries: list[NormalizedTimeEntry], jira_url: str
) -> list[IssueRow]:
    """Build issue table data from normalized entries, aggregated by issue."""
    # Aggregate by issue_key (one row per issue)
    issue_data: dict[str, dict] = {}

    for entry in entries:
        key = entry.issue_key
        if key not in issue_data:
            issue_data[key] = {
                "issue_key": entry.issue_key,
                "issue_title": entry.issue_title,
                "issue_type": entry.issue_type,
                "epic_key": entry.epic_key,
                "epic_title": entry.epic_title,
                "unassigned": False,
                "raw_hours": 0.0,
                "normalized_hours": 0.0,
            }
        if entry.developer == "Unassigned":
            issue_data[key]["unassigned"] = True
        issue_data[key]["raw_hours"] += entry.raw_hours
        issue_data[key]["normalized_hours"] += entry.normalized_hours

    # Build rows sorted by normalized hours
    rows = []
    for data in sorted(issue_data.values(), key=lambda x: -x["normalized_hours"]):
        rows.append(
            IssueRow(
                issue_key=data["issue_key"],
                issue_url=f"{jira_url.rstrip('/')}/browse/{data['issue_key']}",
                issue_title=data["issue_title"],
                issue_type=data["issue_type"],
                epic_key=data["epic_key"],
                epic_title=data["epic_title"],
                raw_hours=round(data["raw_hours"], 2),
                normalized_hours=round(data["normalized_hours"], 2),
                unassigned=data["unassigned"],
            )
        )

    return rows


def _build_issues_no_time_data(
    issues: list, issues_no_time_keys: set[str], jira_url: str
) -> list[IssueRow]:
    """Build issue rows for issues without time entries."""
    rows = []
    for issue in issues:
        if issue.key in issues_no_time_keys:
            rows.append(
                IssueRow(
                    issue_key=issue.key,
                    issue_url=f"{jira_url.rstrip('/')}/browse/{issue.key}",
                    issue_title=issue.summary,
                    issue_type=issue.issue_type,
                    epic_key=issue.epic_key,
                    epic_title=issue.epic_title,
                    raw_hours=0.0,
                    normalized_hours=0.0,
                )
            )
    # Sort by issue key
    return sorted(rows, key=lambda x: x.issue_key)

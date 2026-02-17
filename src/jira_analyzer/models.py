"""Data models for JIRA Utilization Analyzer."""

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class StatusTransition:
    """A single status change event from JIRA's changelog."""

    timestamp: datetime
    from_status: str | None
    to_status: str
    author: str


@dataclass
class AssigneeChange:
    """A change in assignee or developer field from JIRA's changelog."""

    timestamp: datetime
    field: str  # "assignee" or custom developer field name
    from_value: str | None
    to_value: str | None


@dataclass
class Issue:
    """Represents a JIRA issue with relevant fields for analysis."""

    key: str
    title: str
    issue_type: str
    epic_key: str | None
    epic_title: str | None
    status_history: list[StatusTransition]
    assignee_history: list[AssigneeChange]
    current_developer: str | None
    current_assignee: str | None
    parent_key: str | None = None  # non-epic parent (for sub-tasks)


@dataclass
class RawTimeEntry:
    """Calculated raw time for an issue/developer/day before normalization."""

    issue_key: str
    developer: str
    date: date
    raw_hours: float
    is_unassigned: bool = False


@dataclass
class NormalizedTimeEntry:
    """Final output: normalized time for an issue/developer/day."""

    issue_key: str
    issue_title: str
    issue_type: str
    epic_key: str | None
    epic_title: str | None
    developer: str
    date: date
    raw_hours: float
    normalized_hours: float


@dataclass
class EpicSummary:
    """Aggregated view by epic."""

    epic_key: str | None
    epic_title: str | None
    total_hours: float
    percentage: float


@dataclass
class AnalysisResult:
    """Complete result of an analysis run."""

    jql_query: str
    start_date: date
    end_date: date
    total_issues: int
    issues_with_time: int
    issues_with_no_time: int
    unassigned_issues: int
    entries: list[NormalizedTimeEntry]
    no_time_issue_keys: list[str] = field(default_factory=list)
    unassigned_issue_keys: list[str] = field(default_factory=list)
    epic_summaries: list[EpicSummary] | None = None
    from_cache: bool = False


@dataclass
class RoadmapEpic:
    """An epic on the roadmap timeline."""

    key: str
    title: str
    status: str
    status_category: str  # "new" | "indeterminate" | "done"
    start_date: date | None
    end_date: date | None
    url: str


@dataclass
class RoadmapInitiative:
    """An initiative on the roadmap timeline, containing linked epics."""

    key: str
    title: str
    status: str
    status_category: str
    start_date: date | None  # min of epic start dates
    end_date: date | None  # max of epic end dates
    epics: list[RoadmapEpic]
    url: str


@dataclass
class RoadmapResult:
    """Complete result of a roadmap fetch."""

    initiatives: list[RoadmapInitiative]
    jql_query: str
    timeline_start: date
    timeline_end: date
    jira_url: str


def resolve_epic_hierarchy(issues: list[Issue]) -> None:
    """Resolve epic info for sub-tasks via their parent story/task.

    When a sub-task's parent is a Story (not an Epic), it will have
    parent_key set but epic_key=None. This function looks up the parent
    in the issue list and inherits its epic_key/epic_title.
    """
    issue_by_key = {issue.key: issue for issue in issues}
    for issue in issues:
        if issue.epic_key is None and issue.parent_key:
            parent = issue_by_key.get(issue.parent_key)
            if parent and parent.epic_key:
                issue.epic_key = parent.epic_key
                issue.epic_title = parent.epic_title

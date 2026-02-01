"""Data models for JIRA Allocation Analyzer."""

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

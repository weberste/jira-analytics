# Data Model: JIRA Allocation Analyzer

**Date**: 2026-01-31
**Feature**: 001-sprint-allocation

## Core Entities

### Config

Persisted configuration for JIRA connection and analysis settings.

```python
@dataclass
class Config:
    jira_url: str              # e.g., "https://mycompany.atlassian.net"
    jira_email: str            # User email for API auth
    jira_api_token: str        # API token (stored securely)
    active_statuses: list[str] # Default: ["In Progress"]
    developer_field: str | None # Custom field name, e.g., "customfield_10001"
```

**Storage**: `~/.jira-analyzer/config.toml`

---

### Issue

Represents a JIRA issue with relevant fields for analysis.

```python
@dataclass
class Issue:
    key: str                   # e.g., "PROJ-123"
    title: str                 # Issue summary
    issue_type: str            # e.g., "Story", "Bug", "Task"
    epic_key: str | None       # Parent epic key, e.g., "PROJ-50"
    epic_title: str | None     # Parent epic summary
    status_history: list[StatusTransition]
    current_developer: str | None  # Current Developer field value
    current_assignee: str | None   # Current assignee display name
```

**Source**: JIRA REST API `/rest/api/3/search` with `expand=changelog`

---

### StatusTransition

A single status change event from JIRA's changelog.

```python
@dataclass
class StatusTransition:
    timestamp: datetime        # When the transition occurred (UTC)
    from_status: str | None    # Previous status (None if created)
    to_status: str             # New status
    author: str                # Who made the change (display name)
```

**Source**: JIRA issue changelog → `histories[].items[]` where `field == "status"`

---

### AssigneeChange

A change in assignee or developer field from JIRA's changelog.

```python
@dataclass
class AssigneeChange:
    timestamp: datetime        # When the change occurred (UTC)
    field: str                 # "assignee" or "Developer" (custom field)
    from_value: str | None     # Previous value (display name)
    to_value: str | None       # New value (display name)
```

**Source**: JIRA issue changelog → `histories[].items[]` where `field == "assignee"` or custom developer field

---

### RawTimeEntry

Calculated raw time for an issue/developer/day before normalization.

```python
@dataclass
class RawTimeEntry:
    issue_key: str
    developer: str             # Display name or "Unassigned"
    date: date                 # The workday
    raw_hours: float           # Hours before normalization (0-8)
    is_unassigned: bool        # True if developer couldn't be determined
```

**Derived from**: StatusTransition + AssigneeChange data

---

### NormalizedTimeEntry

Final output: normalized time for an issue/developer/day.

```python
@dataclass
class NormalizedTimeEntry:
    issue_key: str
    issue_title: str
    issue_type: str
    epic_key: str | None
    epic_title: str | None
    developer: str
    date: date
    normalized_hours: float    # After scaling to 8h/day/developer
```

**Derived from**: RawTimeEntry after per-developer-per-day normalization

---

### EpicSummary

Aggregated view by epic.

```python
@dataclass
class EpicSummary:
    epic_key: str | None       # None = "No Epic"
    epic_title: str | None
    total_hours: float
    percentage: float          # Of total analyzed time
```

**Derived from**: Aggregation of NormalizedTimeEntry

---

### AnalysisResult

Complete result of an analysis run.

```python
@dataclass
class AnalysisResult:
    jql_query: str
    start_date: date
    end_date: date
    total_issues: int
    issues_with_time: int          # Issues that had activity in active status
    issues_with_no_time: int       # Issues with no activity in timeframe
    unassigned_issues: int         # Issues where developer couldn't be determined
    entries: list[NormalizedTimeEntry]  # Includes "Unassigned" entries
    no_time_issue_keys: list[str]  # For --show-no-time flag
    unassigned_issue_keys: list[str]  # For --show-no-time flag
    epic_summaries: list[EpicSummary] | None  # If --by-epic requested
```

---

## Relationships

```
Config (1) ────── used by ────── Analysis Session

Issue (1) ──┬── has many ──── StatusTransition (N)
            └── has many ──── AssigneeChange (N)

Issue (N) ──── belongs to ──── Epic (1) [optional]

RawTimeEntry (N) ──── derived from ──── Issue + StatusTransition + AssigneeChange

NormalizedTimeEntry (N) ──── normalized from ──── RawTimeEntry (N)
                         [grouped by developer + date, scaled to 8h]

EpicSummary (N) ──── aggregated from ──── NormalizedTimeEntry (N)
```

---

## State Transitions

### Issue Status Flow (for time tracking)

```
[Any Status] ──→ [Active Status] ──→ [Any Status]
                 (e.g., "In Progress")
                      │
                      ▼
              Time tracking starts
                      │
                      ▼
              Time tracking stops
```

**Active window**: Time between entering and leaving an active status.

### Developer Attribution Flow

```
1. Check Developer field at time of active status (from history)
   └── Found? → Use that developer

2. Check Assignee at time of active status (from history)
   └── Found? → Use that assignee

3. Check current Developer field
   └── Found? → Use that developer

4. Check current Assignee
   └── Found? → Use that assignee

5. Mark as "Unassigned" → Include in output with developer="Unassigned"
```

---

## Validation Rules

| Entity | Rule | Error Behavior |
|--------|------|----------------|
| Config.jira_url | Must be valid HTTPS URL | Fail on load |
| Config.jira_email | Must contain @ | Fail on load |
| Config.jira_api_token | Must not be empty | Fail on load |
| Timeframe | start_date <= end_date | Fail before analysis |
| Timeframe | Dates must not be in future | Warning only |
| RawTimeEntry.raw_hours | 0 <= hours <= 8 | Clamp to bounds |
| NormalizedTimeEntry.normalized_hours | Sum per developer per day = 8 | Invariant |

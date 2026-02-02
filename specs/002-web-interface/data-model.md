# Data Model: Web Interface

**Date**: 2026-02-02
**Feature**: 002-web-interface

## Overview

The web interface reuses all core entities from 001-sprint-allocation (Config, Issue, RawTimeEntry, NormalizedTimeEntry, AnalysisResult). This document defines additional entities specific to the web interface layer.

## Web-Specific Entities

### AnalysisRequest

Represents a user's analysis request submitted via the web form.

```python
@dataclass
class AnalysisRequest:
    jql: str               # JQL query string
    from_date: date        # Start of analysis period
    to_date: date          # End of analysis period
```

**Validation Rules**:
- `jql` must not be empty
- `from_date` must be a valid date in YYYY-MM-DD format
- `to_date` must be a valid date in YYYY-MM-DD format
- `from_date` must be <= `to_date`

**Source**: POST form data from web form

---

### WebAnalysisResult

Extended analysis result with web-specific formatting.

```python
@dataclass
class WebAnalysisResult:
    # From core AnalysisResult
    jql_query: str
    start_date: date
    end_date: date
    total_issues: int
    issues_with_time: int
    issues_with_no_time: int
    unassigned_issues: int
    entries: list[NormalizedTimeEntry]
    from_cache: bool

    # Web-specific additions
    epic_chart_data: EpicChartData
    issue_table_data: list[IssueRow]
```

**Source**: Derived from core AnalysisResult with additional transformations

---

### EpicChartData

Data structure for rendering the epic allocation chart.

```python
@dataclass
class EpicChartData:
    labels: list[str]      # Epic names (or "No Epic")
    values: list[float]    # Hours per epic
    percentages: list[float]  # Percentage per epic
    colors: list[str]      # Hex color codes for chart segments
    epic_keys: list[str | None]  # Epic keys for linking (None for "No Epic")
```

**Derivation**:
- Aggregate NormalizedTimeEntry by (epic_key, epic_title)
- Sort by hours descending
- Assign colors from predefined palette
- Calculate percentages from total

---

### IssueRow

Flattened row structure for the issue table.

```python
@dataclass
class IssueRow:
    issue_key: str
    issue_url: str         # Full JIRA URL for linking
    issue_title: str
    issue_type: str
    epic_key: str | None
    epic_title: str | None
    developer: str
    raw_hours: float
    normalized_hours: float
```

**Derivation**: Aggregate NormalizedTimeEntry by issue, sum hours across dates

---

### FormState

Browser-side state for form persistence (stored in sessionStorage).

```javascript
// sessionStorage schema
{
    "jira_analyzer_form": {
        "jql": "project = MYPROJ",
        "from_date": "2026-01-01",
        "to_date": "2026-01-31"
    }
}
```

**Persistence**: Saved on form submit, restored on page load

---

## Relationships

```
AnalysisRequest (1) ──── submitted to ──── Web Route
                                              │
                                              ▼
                                    Core Analysis Pipeline
                                    (jira_client → time_calculator → normalizer)
                                              │
                                              ▼
                              AnalysisResult (from core)
                                              │
                                              ▼
                              WebAnalysisResult (transformed)
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            EpicChartData                    IssueRow (list)
                    │                               │
                    ▼                               ▼
            Chart.js Chart                   HTML Table
```

---

## Data Flow

### Analysis Request Flow

1. User fills form (JQL, from_date, to_date)
2. Form submits POST to `/analyze`
3. Route handler validates AnalysisRequest
4. Core modules execute analysis
5. WebAnalysisResult created with chart/table transformations
6. Template renders with result data
7. JavaScript initializes Chart.js with EpicChartData
8. JavaScript initializes sortable table with IssueRow list

### Chart Interaction Flow

1. User clicks chart segment
2. JavaScript captures epic_key from click event
3. JavaScript filters IssueRow list by epic_key
4. Table re-renders with filtered rows
5. "Clear filter" resets to full list

### Export Flow

1. User clicks "Export CSV"
2. POST to `/export` with current analysis parameters
3. Server re-runs analysis (or uses cached result)
4. Server generates CSV using same format as CLI
5. Response returned with `Content-Disposition: attachment`
6. Browser downloads file

---

## Color Palette

Predefined colors for chart segments (max 12, cycles after):

```python
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
```

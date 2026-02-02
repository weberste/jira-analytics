# Web API Contract: jira-analyzer web

**Date**: 2026-02-02
**Feature**: 002-web-interface

## Overview

The web interface is a local Flask application that provides HTTP endpoints for running JIRA allocation analysis through a browser.

## CLI Command

### `jira-analyzer web`

Start the web interface server.

```bash
jira-analyzer web [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port`, `-p` | int | 5000 | Port to run the server on |
| `--host` | string | "127.0.0.1" | Host to bind to |
| `--open`, `-o` | flag | false | Open browser automatically after starting |
| `--debug` | flag | false | Run in debug mode (auto-reload) |

**Examples**:

```bash
# Start on default port (5000)
jira-analyzer web

# Start on custom port
jira-analyzer web --port 8080

# Start and open browser
jira-analyzer web --open

# Development mode with auto-reload
jira-analyzer web --debug
```

---

## HTTP Endpoints

### GET `/`

Render the main analysis page with the query form.

**Response**: HTML page

**Behavior**:
- If configuration exists: Render form ready for input
- If configuration missing: Render setup instructions with link to CLI commands

---

### POST `/analyze`

Run an analysis and return results.

**Request**: Form data (application/x-www-form-urlencoded)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jql` | string | Yes | JQL query to select issues |
| `from_date` | string | Yes | Start date (YYYY-MM-DD) |
| `to_date` | string | Yes | End date (YYYY-MM-DD) |

**Response**: HTML partial (results section) or full page

**Success Response** (200):
- HTML containing:
  - Summary statistics panel
  - Epic allocation chart (Chart.js data embedded as JSON)
  - Epic allocation table
  - Issue breakdown table (hidden by default, shown via tab)

**Error Responses**:

| Status | Condition | Response |
|--------|-----------|----------|
| 400 | Invalid date format | HTML with error message |
| 400 | from_date > to_date | HTML with error message |
| 400 | Empty JQL query | HTML with error message |
| 400 | Invalid JQL syntax | HTML with JIRA error message |
| 401 | JIRA auth failed | HTML with credentials error |
| 429 | JIRA rate limited | HTML with retry message |
| 503 | Config not found | HTML with setup instructions |

---

### POST `/export`

Export analysis results as CSV.

**Request**: Form data (application/x-www-form-urlencoded)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jql` | string | Yes | JQL query (same as analysis) |
| `from_date` | string | Yes | Start date (YYYY-MM-DD) |
| `to_date` | string | Yes | End date (YYYY-MM-DD) |

**Success Response** (200):
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="allocation-YYYY-MM-DD.csv"`
- Body: CSV data matching CLI format

**CSV Format**:
```csv
issue_key,issue_title,issue_type,epic_key,epic_title,developer,date,raw_hours,normalized_hours
PROJ-101,Fix login bug,Bug,PROJ-50,Auth Epic,Alice,2026-01-02,4.00,3.50
...
```

**Error Responses**: Same as `/analyze`

---

### GET `/health`

Health check endpoint.

**Response** (200):
```json
{
    "status": "ok",
    "config_loaded": true,
    "version": "0.1.0"
}
```

**Response** (503) if config missing:
```json
{
    "status": "error",
    "config_loaded": false,
    "message": "Configuration not found"
}
```

---

## Page Structure

### Main Page (`/`)

```
┌─────────────────────────────────────────────────────────────────┐
│  JIRA Allocation Analyzer                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ JQL Query:  [______________________________________]    │   │
│  │ From:       [__________]  To: [__________]              │   │
│  │                                    [Analyze]            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Summary                               │   │
│  │  Issues: 47 | With time: 45 | No time: 2 | Unassigned: 2│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────┬──────────────────────────────────┐   │
│  │                      │  Epic         Hours    %         │   │
│  │    [PIE CHART]       │  ─────────────────────────────   │   │
│  │                      │  Auth Epic    28.5    35.6%      │   │
│  │                      │  Profile      24.0    30.0%      │   │
│  │                      │  No Epic      11.5    14.4%      │   │
│  │                      │  ─────────────────────────────   │   │
│  │                      │  TOTAL        80.0    100%       │   │
│  └──────────────────────┴──────────────────────────────────┘   │
│                                                                 │
│  [Epic View]  [Issue View]                    [Export CSV]      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Issue    Title              Type   Epic      Hours      │   │
│  │ ──────────────────────────────────────────────────────  │   │
│  │ PROJ-103 Refactor auth      Task   PROJ-50   16.0       │   │
│  │ PROJ-101 Fix login bug      Bug    PROJ-50   12.5       │   │
│  │ ...                                                     │   │
│  │                                                         │   │
│  │ [1] [2] [3] ... [5]  (pagination)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## JavaScript API

### Form State

```javascript
// Save form state
function saveFormState() {
    sessionStorage.setItem('jira_analyzer_form', JSON.stringify({
        jql: document.getElementById('jql').value,
        from_date: document.getElementById('from_date').value,
        to_date: document.getElementById('to_date').value
    }));
}

// Restore form state
function restoreFormState() {
    const saved = sessionStorage.getItem('jira_analyzer_form');
    if (saved) {
        const state = JSON.parse(saved);
        document.getElementById('jql').value = state.jql || '';
        document.getElementById('from_date').value = state.from_date || '';
        document.getElementById('to_date').value = state.to_date || '';
    }
}
```

### Chart Interaction

```javascript
// Chart click handler for filtering
chart.options.onClick = function(event, elements) {
    if (elements.length > 0) {
        const index = elements[0].index;
        const epicKey = chartData.epicKeys[index];
        filterTableByEpic(epicKey);
    }
};

// Filter table by epic
function filterTableByEpic(epicKey) {
    // Show only rows matching epicKey
    // Show "Clear filter" button
}

// Clear filter
function clearFilter() {
    // Show all rows
    // Hide "Clear filter" button
}
```

### Table Pagination

```javascript
const ROWS_PER_PAGE = 100;
let currentPage = 1;

function renderTable(page) {
    const start = (page - 1) * ROWS_PER_PAGE;
    const end = start + ROWS_PER_PAGE;
    const pageData = allRows.slice(start, end);
    // Render pageData to table
    // Update pagination controls
}
```

---

## Error Display

All errors are displayed in a dismissible alert box above the results area:

```html
<div class="alert alert-error">
    <span class="alert-message">Error message here</span>
    <button class="alert-close">&times;</button>
</div>
```

Error messages are user-friendly and include guidance:

| Error Type | Message |
|------------|---------|
| Config missing | "Configuration not found. Run `jira-analyzer config init` in your terminal to set up." |
| Auth failed | "JIRA authentication failed. Check your credentials with `jira-analyzer config show`." |
| Invalid JQL | "Invalid JQL query: {JIRA error}. Check your query syntax." |
| Rate limited | "JIRA rate limit exceeded. Please wait a moment and try again." |
| No issues | "No issues found matching your query." |
| No activity | "No work activity found in the specified timeframe." |

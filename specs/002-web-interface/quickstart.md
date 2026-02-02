# Quickstart: JIRA Allocation Analyzer Web Interface

**Date**: 2026-02-02
**Feature**: 002-web-interface

## Prerequisites

- Python 3.11 or higher
- JIRA Allocation Analyzer CLI installed and configured
- JIRA API credentials configured via `jira-analyzer config init`

## Installation

### If you have the CLI already installed:

```bash
# Install web dependencies
pip install jira-analyzer[web]
```

### Fresh installation:

```bash
# Clone and install with web support
git clone https://github.com/your-org/jira-analytics.git
cd jira-analytics
pip install -e ".[web]"
```

## Verify Configuration

Before starting the web interface, ensure your CLI is configured:

```bash
# Check configuration
jira-analyzer config show

# If not configured, run setup
jira-analyzer config init
```

## Starting the Web Interface

```bash
# Start on default port (5000)
jira-analyzer web

# Start on custom port
jira-analyzer web --port 8080

# Start and automatically open browser
jira-analyzer web --open
```

You'll see output like:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to stop
```

Open your browser to `http://localhost:5000` (or use `--open` flag).

## Using the Web Interface

### 1. Enter Your Query

Fill in the analysis form:
- **JQL Query**: Enter a JIRA query (e.g., `project = MYPROJ AND sprint = "Sprint 23"`)
- **From Date**: Start of the analysis period
- **To Date**: End of the analysis period

Click **Analyze** to run the analysis.

### 2. View Results

After analysis completes, you'll see:

- **Summary Statistics**: Total issues, issues with time, issues without time
- **Epic Allocation Chart**: Visual pie chart showing time distribution by epic
- **Epic Table**: Breakdown of hours and percentages per epic
- **Issue Table**: Detailed per-issue breakdown (click "Issue View" tab)

### 3. Interactive Features

**Chart Filtering**:
- Click any segment in the pie chart to filter the issue table to that epic
- Click "Clear Filter" to show all issues again
- Hover over segments to see tooltips with details

**Table Sorting**:
- Click column headers to sort the issue table
- Default sort is by hours (highest first)

**Issue Links**:
- Click any issue key to open that issue in JIRA (new tab)

### 4. Export Results

Click **Export CSV** to download the results as a CSV file. The format matches the CLI output exactly, so you can use it in spreadsheets or other tools.

## Common JQL Queries

```
# All issues in a sprint
project = MYPROJ AND sprint = "Sprint 23"

# Issues in a date range
project = MYPROJ AND created >= 2026-01-01 AND created <= 2026-01-31

# Specific issue types
project = MYPROJ AND issuetype IN (Story, Bug)

# Multiple projects
project IN (PROJ1, PROJ2)

# Excluding certain types
project = MYPROJ AND issuetype NOT IN (Epic, Sub-task)
```

## Troubleshooting

### "Configuration not found"

The web interface uses the same configuration as the CLI. Set it up first:

```bash
jira-analyzer config init
```

### "Authentication failed"

Your JIRA credentials may be incorrect or expired:

1. Check current config: `jira-analyzer config show`
2. Generate a new API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. Update: `jira-analyzer config set jira_api_token <new-token>`

### "No issues found"

- Test your JQL query directly in JIRA's issue search
- Verify you have permission to view those issues
- Check that issues exist matching your criteria

### "No work activity found"

The issues exist but had no "In Progress" time during your date range:

- Expand your date range
- Add more active statuses: `jira-analyzer config set active_statuses "In Progress,In Review"`

### Port already in use

Another application is using port 5000:

```bash
# Use a different port
jira-analyzer web --port 8080
```

### Server won't start

Check that Flask is installed:

```bash
pip install flask
# Or reinstall with web extras
pip install jira-analyzer[web]
```

## Comparing with CLI

The web interface provides the same analysis as the CLI. For the same inputs, results will be identical:

| Web Interface | CLI Equivalent |
|---------------|----------------|
| Enter JQL, dates, click Analyze | `jira-analyzer utilization --jql "..." --from ... --to ...` |
| View Epic allocation (default) | `jira-analyzer utilization ...` (epic view is default) |
| Click "Issue View" tab | `jira-analyzer utilization ... --by-issue` |
| Click "Export CSV" | `jira-analyzer utilization ... --output csv --output-file file.csv` |

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

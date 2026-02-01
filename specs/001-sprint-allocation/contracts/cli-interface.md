# CLI Interface Contract: jira-analyzer

**Date**: 2026-01-31
**Feature**: 001-sprint-allocation

## Command Overview

```
jira-analyzer <command> [options]

Commands:
  analyze     Analyze time allocation for issues matching a JQL query
  config      Manage configuration (init, show, set)
  version     Show version information
```

---

## `jira-analyzer analyze`

Main command to analyze time allocation.

### Usage

```bash
jira-analyzer analyze --jql <query> --from <date> --to <date> [options]
```

### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--jql`, `-q` | string | JQL query to select issues |
| `--from`, `-f` | date | Start date (YYYY-MM-DD) |
| `--to`, `-t` | date | End date (YYYY-MM-DD) |

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--by-epic` | flag | false | Aggregate results by parent epic |
| `--output`, `-o` | string | "table" | Output format: "table" or "csv" |
| `--output-file` | path | stdout | File path for CSV output |
| `--show-incomplete` | flag | false | List issue keys with no time spent or no assignee |

### Examples

```bash
# Basic analysis for a sprint
jira-analyzer analyze \
  --jql 'project = MYPROJ AND sprint = "Sprint 23"' \
  --from 2026-01-01 \
  --to 2026-01-14

# Analysis with epic aggregation
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --by-epic

# Export to CSV
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --output csv \
  --output-file allocation.csv
```

### Output: Table Format (default)

```
Fetching issues... 47 found
Retrieving history... [████████████████████] 47/47
Calculating time...

═══════════════════════════════════════════════════════════════════════════════
                        Time Allocation Report
                     2026-01-01 to 2026-01-14
═══════════════════════════════════════════════════════════════════════════════

Issue      Title                    Type    Epic         Developer    Hours
────────────────────────────────────────────────────────────────────────────────
PROJ-101   Fix login bug            Bug     PROJ-50      Alice        12.5
PROJ-102   Add user profile         Story   PROJ-51      Alice         8.0
PROJ-103   Refactor auth module     Task    PROJ-50      Bob          16.0
PROJ-104   Update dependencies      Task    —            Bob           4.0
PROJ-199   Legacy cleanup           Task    —            Unassigned    8.0
PROJ-200   Spike: new framework     Spike   —            Unassigned    4.0
...

═══════════════════════════════════════════════════════════════════════════════
                              Summary
═══════════════════════════════════════════════════════════════════════════════
Total issues analyzed: 47
Issues with time spent: 45 (95.7%)
Issues with no time spent: 2 (4.3%)
Issues without assignee: 2 (4.3%)
```

### Output: Table Format with `--show-incomplete`

When `--show-incomplete` is passed, issue keys are listed after the summary:

```
═══════════════════════════════════════════════════════════════════════════════
                              Summary
═══════════════════════════════════════════════════════════════════════════════
Total issues analyzed: 47
Issues with time spent: 45 (95.7%)
Issues with no time spent: 2 (4.3%)
Issues without assignee: 2 (4.3%)

Issues with no time spent:
  PROJ-205, PROJ-210

Issues without assignee:
  PROJ-199, PROJ-200
```

### Output: Table Format with `--by-epic`

```
═══════════════════════════════════════════════════════════════════════════════
                        Epic Allocation Summary
                     2026-01-01 to 2026-01-14
═══════════════════════════════════════════════════════════════════════════════

Epic         Title                         Hours      %
────────────────────────────────────────────────────────────────────────────────
PROJ-50      Authentication Improvements    28.5    35.6%
PROJ-51      User Profile Feature           24.0    30.0%
PROJ-52      Performance Optimization       16.0    20.0%
—            No Epic                        11.5    14.4%
────────────────────────────────────────────────────────────────────────────────
             TOTAL                          80.0   100.0%
```

### Output: CSV Format

```csv
issue_key,issue_title,issue_type,epic_key,epic_title,developer,date,normalized_hours
PROJ-101,Fix login bug,Bug,PROJ-50,Authentication Improvements,Alice,2026-01-02,4.0
PROJ-101,Fix login bug,Bug,PROJ-50,Authentication Improvements,Alice,2026-01-03,8.0
PROJ-102,Add user profile,Story,PROJ-51,User Profile Feature,Alice,2026-01-03,0.0
...
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Configuration error (missing config, invalid credentials) |
| 2 | Invalid arguments (bad JQL, invalid date format) |
| 3 | JIRA API error (auth failed, rate limited after retries) |
| 4 | No data found (query returned no issues or no activity in timeframe) |

---

## `jira-analyzer config`

Manage configuration settings.

### Subcommands

#### `jira-analyzer config init`

Interactive configuration setup.

```bash
jira-analyzer config init
```

**Prompts**:
1. JIRA site URL (e.g., https://mycompany.atlassian.net)
2. Email address
3. API token (hidden input)
4. Active statuses (comma-separated, default: "In Progress")
5. Developer custom field name (optional)

**Creates**: `~/.jira-analyzer/config.toml`

#### `jira-analyzer config show`

Display current configuration (API token masked).

```bash
jira-analyzer config show
```

**Output**:
```
Configuration (~/.jira-analyzer/config.toml)

jira_url: https://mycompany.atlassian.net
jira_email: user@example.com
jira_api_token: ****...****
active_statuses: ["In Progress"]
developer_field: customfield_10001
```

#### `jira-analyzer config set <key> <value>`

Update a single configuration value.

```bash
jira-analyzer config set active_statuses "In Progress,In Review"
jira-analyzer config set developer_field customfield_10001
```

---

## `jira-analyzer version`

Display version information.

```bash
jira-analyzer version
```

**Output**:
```
jira-analyzer 0.1.0
Python 3.11.5
```

---

## Configuration File Format

**Location**: `~/.jira-analyzer/config.toml`

```toml
# JIRA Analyzer Configuration

[jira]
url = "https://mycompany.atlassian.net"
email = "user@example.com"
api_token = "your-api-token-here"

[analysis]
# Statuses that indicate active work (time is counted)
active_statuses = ["In Progress"]

# Custom field name for Developer (optional)
# Leave empty to use Assignee only
developer_field = "customfield_10001"
```

---

## Error Messages

| Scenario | Message |
|----------|---------|
| No config file | `Configuration not found. Run 'jira-analyzer config init' to set up.` |
| Invalid credentials | `Authentication failed. Check your email and API token.` |
| Invalid JQL | `Invalid JQL query: {JIRA error message}` |
| Rate limited | `Rate limited by JIRA. Retrying in {N} seconds... (attempt {M}/3)` |
| Rate limit exhausted | `JIRA API rate limit exceeded after 3 retries. Try again later.` |
| No issues found | `No issues found matching query: {JQL}` |
| No activity in timeframe | `No work activity found in the specified timeframe.` |
| Invalid date format | `Invalid date format '{input}'. Use YYYY-MM-DD.` |
| Start after end | `Start date must be before or equal to end date.` |

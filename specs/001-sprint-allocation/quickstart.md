# Quickstart: JIRA Allocation Analyzer

**Date**: 2026-01-31
**Feature**: 001-sprint-allocation

## Prerequisites

- Python 3.11 or higher
- Access to a JIRA Cloud instance
- JIRA API token ([create one here](https://id.atlassian.com/manage-profile/security/api-tokens))

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/your-org/jira-analytics.git
cd jira-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### From PyPI (Future)

```bash
pip install jira-analyzer
```

## Initial Setup

Run the interactive configuration wizard:

```bash
jira-analyzer config init
```

You'll be prompted for:
1. **JIRA site URL**: e.g., `https://mycompany.atlassian.net`
2. **Email**: Your JIRA account email
3. **API token**: Your JIRA API token (hidden input)
4. **Active statuses**: Statuses that indicate work in progress (default: "In Progress")
5. **Developer field**: Custom field name if your team uses one (optional)

This creates `~/.jira-analyzer/config.toml`.

## Basic Usage

### Analyze a Sprint

```bash
jira-analyzer analyze \
  --jql 'project = MYPROJ AND sprint = "Sprint 23"' \
  --from 2026-01-01 \
  --to 2026-01-14
```

### Analyze by Date Range

```bash
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31
```

### View by Epic

```bash
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --by-epic
```

### Export to CSV

```bash
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --output csv \
  --output-file allocation.csv
```

## Understanding the Output

### Time Calculation

The tool calculates time based on how long issues were in "active" statuses (default: "In Progress"):

1. **Raw time**: Hours an issue spent in active status per day
   - Full day in progress = 8 hours
   - Partial day = actual hours (8am-4pm workday assumed)

2. **Normalized time**: Adjusted to account for parallel work
   - If a developer worked on 3 issues totaling 12 raw hours, each is scaled proportionally to sum to 8 hours
   - This prevents over-counting when someone works on multiple issues

### Data Quality

- **Unassigned issues**: Reported separately (not normalized)
- **Missing history**: Issues without status transitions are excluded

## Common JQL Queries

```bash
# All issues in a project for a quarter
--jql 'project = MYPROJ AND created >= 2026-01-01 AND created <= 2026-03-31'

# Specific sprint
--jql 'project = MYPROJ AND sprint = "Sprint 23"'

# Multiple projects
--jql 'project IN (PROJ1, PROJ2)'

# Specific issue types
--jql 'project = MYPROJ AND issuetype IN (Story, Bug)'

# Excluding certain types
--jql 'project = MYPROJ AND issuetype NOT IN (Epic, Sub-task)'

# Team/assignee filter (for pre-filtering, not attribution)
--jql 'project = MYPROJ AND assignee IN (alice, bob, charlie)'
```

## Troubleshooting

### "Configuration not found"

Run `jira-analyzer config init` to create the config file.

### "Authentication failed"

1. Verify your email is correct
2. Generate a new API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. Update with `jira-analyzer config set jira_api_token <new-token>`

### "No issues found"

1. Test your JQL query in JIRA's issue search first
2. Check project permissions for your account

### "No work activity found"

The issues exist but had no "In Progress" time during your timeframe. Either:
1. Expand your date range
2. Add more active statuses: `jira-analyzer config set active_statuses "In Progress,In Review"`

### Rate Limiting

The tool automatically retries with exponential backoff. If you see repeated rate limit errors:
1. Wait a few minutes before retrying
2. Reduce the scope of your JQL query
3. Narrow your date range

## Next Steps

- Explore `jira-analyzer --help` for all options
- Check `jira-analyzer analyze --help` for analysis-specific options
- Review [CLI Interface](./contracts/cli-interface.md) for full command reference

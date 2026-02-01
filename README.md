# JIRA Allocation Analyzer

CLI tool to estimate time allocation from JIRA issues based on status transition history — without requiring developers to log time.

## Features

- Analyze issues matching any JQL query within a timeframe
- Calculate normalized time per developer per day (max 7 hours, only scales down)
- Handle partial days, weekends, and parallel work
- Developer attribution from changelog history
- Epic aggregation view (default) or detailed per-issue breakdown
- Local caching with 24-hour expiry to avoid redundant API calls
- CSV export for further analysis

## Installation

### Prerequisites

- Python 3.11 or higher
- Access to a JIRA Cloud instance
- [JIRA API token](https://id.atlassian.com/manage-profile/security/api-tokens)

### Install from Source

```bash
git clone https://github.com/YOUR_USERNAME/jira-analytics.git
cd jira-analytics
pip install -e .
```

### Install with Dev Dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure

```bash
jira-analyzer config init
```

You'll be prompted for:
- JIRA site URL (e.g., `https://mycompany.atlassian.net`)
- Email address
- API token
- Active statuses (default: "In Progress")
- Developer custom field (optional)

### 2. Analyze

```bash
# Basic analysis (epic aggregation by default)
jira-analyzer analyze \
  --jql 'project = MYPROJ AND sprint = "Sprint 23"' \
  --from 2026-01-01 \
  --to 2026-01-14

# Detailed per-issue breakdown
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --by-issue

# Force fresh data (bypass cache)
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --no-cache

# Show issues with incomplete data
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --show-incomplete

# Export to CSV
jira-analyzer analyze \
  --jql 'project = MYPROJ' \
  --from 2026-01-01 \
  --to 2026-01-31 \
  --output csv \
  --output-file allocation.csv
```

### 3. View/Update Configuration

```bash
jira-analyzer config show
jira-analyzer config set active_statuses "In Progress,In Review"
```

## Development

### Setup

```bash
# Clone and install in development mode
git clone https://github.com/YOUR_USERNAME/jira-analytics.git
cd jira-analytics
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Making Changes

After editing code, changes are immediately available (editable install):

```bash
# Edit any file in src/jira_analyzer/
# Then just run:
jira-analyzer analyze --jql "..." --from ... --to ...
```

No reinstall needed — `pip install -e .` creates a link to your source.

### Running Tests

```bash
pytest                      # Run all tests
pytest tests/unit/          # Unit tests only
pytest -v                   # Verbose output
pytest --cov=jira_analyzer  # With coverage
```

### Code Quality

```bash
ruff check src/             # Linting
ruff format src/            # Formatting
mypy src/                   # Type checking
```

### Project Structure

```
src/jira_analyzer/
├── cli.py              # Typer CLI commands
├── config.py           # Configuration management
├── models.py           # Data models
├── jira_client.py      # JIRA API client with retry
├── time_calculator.py  # Raw time calculation
├── normalizer.py       # 7h/day max normalization (scale down only)
├── cache.py            # Local caching with 24h expiry
├── output.py           # Table/CSV formatting
```

## Working with Speckit

This project uses [Speckit](https://github.com/your-org/speckit) for specification-driven development.

### Feature Artifacts

Design documents are in `specs/001-sprint-allocation/`:

| File | Purpose |
|------|---------|
| `spec.md` | [Feature specification](specs/001-sprint-allocation/spec.md) (requirements, user stories) |
| `plan.md` | [Implementation plan](specs/001-sprint-allocation/plan.md) (tech stack, architecture) |
| `tasks.md` | [Task breakdown](specs/001-sprint-allocation/tasks.md) with dependencies |
| `data-model.md` | [Entity definitions](specs/001-sprint-allocation/data-model.md) |
| `contracts/` | [CLI interface contract](specs/001-sprint-allocation/contracts/cli-interface.md) |
| `quickstart.md` | [Usage guide](specs/001-sprint-allocation/quickstart.md) |

### Continue Development

```bash
# Switch to feature branch
git checkout 001-sprint-allocation

# View remaining tasks
cat specs/001-sprint-allocation/tasks.md

# Continue implementation (Phase 4-7)
# Use Claude Code with: /speckit.implement

# Or manually implement tasks from tasks.md
```

### Start a New Feature

```bash
# Create new feature spec
/speckit.specify "Your feature description"

# Clarify requirements
/speckit.clarify

# Generate implementation plan
/speckit.plan

# Generate tasks
/speckit.tasks

# Implement
/speckit.implement
```

### Speckit Commands Reference

| Command | Purpose |
|---------|---------|
| `/speckit.specify` | Create feature specification |
| `/speckit.clarify` | Refine spec with Q&A |
| `/speckit.plan` | Generate implementation plan |
| `/speckit.tasks` | Generate task breakdown |
| `/speckit.implement` | Execute implementation tasks |
| `/speckit.analyze` | Cross-artifact consistency check |

## Current Status

**MVP Complete** (Phase 1-3):
- [x] Core analysis with normalized time (max 7h/day, scale down only)
- [x] Partial day handling (8am-4pm workday boundaries)
- [x] Developer attribution from changelog history
- [x] Epic aggregation (default view)
- [x] Per-issue breakdown (`--by-issue`)
- [x] CSV export with raw and normalized hours
- [x] Configuration management
- [x] Local caching with 24h expiry (`--no-cache` to bypass)
- [x] Incomplete issue reporting (`--show-incomplete`)

**Remaining** (Phase 4-7):
- [ ] Unit and integration tests
- [ ] Additional error handling polish

See `specs/001-sprint-allocation/tasks.md` for full task list.

## License

MIT

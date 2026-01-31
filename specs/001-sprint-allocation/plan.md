# Implementation Plan: JIRA Allocation Analyzer CLI

**Branch**: `001-sprint-allocation` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-sprint-allocation/spec.md`

## Summary

CLI tool to estimate actual time allocation per JIRA issue based on status transition history. Analyzes issues matching a JQL query within a specified timeframe, calculates normalized time per developer per day (8-hour workday), and outputs per-issue allocation data with optional epic aggregation and CSV export.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Typer (CLI), jira-python (JIRA API), Rich (output), tenacity (retry), python-dateutil (dates)
**Storage**: TOML config file (~/.jira-analyzer/config.toml)
**Testing**: pytest + pytest-mock + responses (HTTP mocking)
**Target Platform**: Cross-platform CLI (macOS, Linux, Windows)
**Project Type**: Single project (pip-installable package)
**Performance Goals**: 60 seconds for 500 issues (excluding JIRA API latency)
**Constraints**: JIRA Cloud only, API token auth, exponential backoff for rate limits
**Scale/Scope**: Typical usage 100-500 issues per query

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> Constitution file contains template placeholders only. Proceeding with standard best practices:
> - Single project structure (CLI tool)
> - Unit + integration tests
> - Clean separation of concerns (API client, business logic, CLI)

**Status**: PASS (no specific gates defined)

## Project Structure

### Documentation (this feature)

```text
specs/001-sprint-allocation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── jira_analyzer/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # Typer CLI commands
│   ├── config.py            # Configuration loading/saving
│   ├── models.py            # Data models (Issue, TimeEntry, etc.)
│   ├── jira_client.py       # JIRA API wrapper with retry logic
│   ├── time_calculator.py   # Raw time calculation from status history
│   ├── normalizer.py        # Per-developer-per-day normalization
│   ├── aggregator.py        # Epic aggregation
│   └── output.py            # Table and CSV formatters

tests/
├── unit/
│   ├── test_time_calculator.py
│   ├── test_normalizer.py
│   ├── test_aggregator.py
│   └── test_config.py
├── integration/
│   └── test_jira_client.py  # With mocked HTTP responses
└── fixtures/
    ├── sample_issues.json
    └── sample_changelog.json

pyproject.toml               # Package configuration
```

**Structure Decision**: Single project CLI structure with clear separation between JIRA integration, business logic, and CLI presentation layers.

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Generated Artifacts

| Artifact | Description |
|----------|-------------|
| [research.md](./research.md) | Technology decisions and rationale |
| [data-model.md](./data-model.md) | Entity definitions and relationships |
| [contracts/cli-interface.md](./contracts/cli-interface.md) | CLI command specifications |
| [quickstart.md](./quickstart.md) | Getting started guide |

---

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Run `/speckit.implement` to execute tasks
3. Or proceed with manual implementation following this plan

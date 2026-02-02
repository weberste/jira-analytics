# Implementation Plan: Web Interface

**Branch**: `002-web-interface` | **Date**: 2026-02-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-web-interface/spec.md`

## Summary

Web-based UI for the JIRA Allocation Analyzer that provides the same analysis capabilities as the CLI. Users can enter JQL queries and date ranges via a browser interface, view results as interactive charts and tables, filter by clicking chart segments, and export data to CSV. Reuses existing core modules (time_calculator, normalizer, jira_client) with a new web presentation layer.

## Technical Context

**Language/Version**: Python 3.11+ (backend), HTML/CSS/JavaScript (frontend)
**Primary Dependencies**: Flask (web framework), Chart.js (visualization), existing jira_analyzer modules
**Storage**: Reuses existing TOML config file (~/.jira-analyzer/config.toml), browser sessionStorage for form state
**Testing**: pytest + pytest-flask (backend), manual browser testing (frontend)
**Target Platform**: Local web server, modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Single project extension (adds web module to existing package)
**Performance Goals**: Chart renders in <2 seconds after data received, UI interaction time <30 seconds
**Constraints**: Single-user local deployment, no authentication, reuses CLI configuration
**Scale/Scope**: Same as CLI (100-500 issues typical)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> Constitution file contains template placeholders only. Proceeding with standard best practices:
> - Extends existing single project structure (adds web module)
> - Reuses core business logic modules
> - Clean separation: web routes → core analysis → JIRA API

**Status**: PASS (no specific gates defined)

## Project Structure

### Documentation (this feature)

```text
specs/002-web-interface/
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
│   ├── __main__.py          # Entry point (existing)
│   ├── cli.py               # CLI commands (existing)
│   ├── config.py            # Configuration (existing, reused)
│   ├── models.py            # Data models (existing, reused)
│   ├── jira_client.py       # JIRA API (existing, reused)
│   ├── time_calculator.py   # Time calculation (existing, reused)
│   ├── normalizer.py        # Normalization (existing, reused)
│   ├── cache.py             # Caching (existing, reused)
│   ├── output.py            # CLI formatters (existing)
│   │
│   └── web/                 # NEW: Web interface module
│       ├── __init__.py
│       ├── app.py           # Flask application factory
│       ├── routes.py        # HTTP route handlers
│       ├── analysis.py      # Analysis orchestration (bridges web → core)
│       ├── static/
│       │   ├── css/
│       │   │   └── styles.css
│       │   └── js/
│       │       ├── app.js           # Main application logic
│       │       └── charts.js        # Chart.js configuration
│       └── templates/
│           ├── base.html            # Base template with layout
│           ├── index.html           # Main analysis page
│           └── partials/
│               ├── form.html        # Query form partial
│               ├── results.html     # Results container partial
│               └── error.html       # Error display partial

tests/
├── unit/
│   └── web/
│       ├── test_routes.py
│       └── test_analysis.py
└── integration/
    └── test_web_app.py      # Full request/response tests

pyproject.toml               # Add flask dependency
```

**Structure Decision**: Extends existing single project by adding a `web/` submodule. This keeps all code in one installable package while maintaining clear separation between CLI and web interfaces. Both interfaces share the same core analysis modules.

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
| [contracts/web-api.md](./contracts/web-api.md) | Web API specifications |
| [quickstart.md](./quickstart.md) | Getting started guide |

---

## Next Steps

1. Run `/speckit.tasks` to generate implementation tasks
2. Run `/speckit.implement` to execute tasks
3. Or proceed with manual implementation following this plan

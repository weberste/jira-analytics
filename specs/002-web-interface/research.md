# Research: Web Interface

**Feature**: 002-web-interface
**Date**: 2026-02-02

## Technology Decisions

### Web Framework: Flask

**Decision**: Use Flask as the web framework.

**Rationale**:
- Lightweight and simple - appropriate for a single-user local tool
- Excellent integration with existing Python codebase
- Minimal boilerplate, easy to add to existing package
- Jinja2 templating built-in for server-rendered HTML
- Large ecosystem and well-documented

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| FastAPI | More complex, async not needed for single-user local app |
| Django | Too heavyweight for this use case, unnecessary features |
| Streamlit | Less control over UI, harder to match specific UX requirements |
| Pure JavaScript SPA | Would require separate build tooling, more complexity |

---

### Charting Library: Chart.js

**Decision**: Use Chart.js for data visualization.

**Rationale**:
- Simple, well-documented JavaScript library
- No build step required - can use via CDN or bundled file
- Built-in interactivity (tooltips, click events)
- Responsive by default
- Supports pie and bar charts needed for epic allocation

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| D3.js | More powerful but much steeper learning curve, overkill for simple charts |
| Plotly | Heavier, requires more setup |
| Apache ECharts | More complex configuration |
| Matplotlib (server-side) | Static images, no interactivity |

---

### Frontend Approach: Server-Rendered with JavaScript Enhancement

**Decision**: Use server-rendered HTML (Jinja2 templates) with JavaScript for interactivity.

**Rationale**:
- Simpler than a full SPA - no build tooling, bundlers, or frontend framework
- Analysis requests naturally fit request/response model
- JavaScript only needed for charts and form state
- Faster initial page load
- Easier to maintain as part of Python package

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| React/Vue SPA | Adds build complexity, separate dev server, more tooling |
| HTMX | Good option but adds another dependency; vanilla JS sufficient |
| Fully static pages | Can't support interactive chart filtering |

---

### Form State Persistence: sessionStorage

**Decision**: Use browser sessionStorage to remember last-used query and dates.

**Rationale**:
- Built into browsers, no additional dependencies
- Persists across page refreshes within session
- Automatically cleared when browser closes
- Simple key-value API

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| localStorage | Persists too long, might confuse users with stale queries |
| Server-side sessions | Adds complexity, not needed for single-user tool |
| URL parameters | Makes URLs unwieldy, not user-friendly |

---

### CSV Export: Server-Generated Download

**Decision**: Generate CSV on server and return as downloadable file.

**Rationale**:
- Reuses existing CSV generation logic from CLI
- Guarantees format matches CLI output (FR-014)
- Works reliably across all browsers
- No client-side CSV generation library needed

**Alternatives Considered**:
| Alternative | Why Rejected |
|-------------|--------------|
| Client-side CSV generation | Would need to duplicate formatting logic, risk format mismatch |
| JSON download | Users specifically want CSV for spreadsheet import |

---

## Architecture Decisions

### Reusing Core Modules

**Decision**: Import and use existing modules directly (config, jira_client, time_calculator, normalizer, cache).

**Rationale**:
- Ensures analysis results match CLI exactly (SC-003)
- No code duplication
- Bug fixes in core benefit both interfaces
- Reduces implementation effort significantly

**Implementation**:
```python
# web/analysis.py
from jira_analyzer.config import load_config
from jira_analyzer.jira_client import JiraClient
from jira_analyzer.time_calculator import calculate_raw_time
from jira_analyzer.normalizer import normalize_time_entries
from jira_analyzer.cache import get_cached_issues, save_to_cache
```

---

### Error Handling Strategy

**Decision**: Catch exceptions in route handlers, convert to user-friendly messages, return appropriate HTTP status codes.

**Mapping**:
| Exception | HTTP Status | User Message |
|-----------|-------------|--------------|
| FileNotFoundError (config) | 503 | Configuration not found. Run `jira-analyzer config init` first. |
| ValueError (config) | 503 | Invalid configuration. Check your settings with `jira-analyzer config show`. |
| AuthenticationError | 401 | JIRA authentication failed. Check your credentials. |
| RateLimitError | 429 | JIRA rate limit exceeded. Please try again later. |
| ValueError (JQL) | 400 | Invalid JQL query. Please check your syntax. |
| No issues found | 200 | No issues found matching your query. |
| No activity | 200 | No work activity found in the specified timeframe. |

---

### Large Result Set Handling

**Decision**: Implement client-side pagination for issue tables (100 rows per page).

**Rationale**:
- Keeps initial render fast
- Browser handles pagination state
- Server returns all data in one response (typical sizes 100-500 issues are manageable)
- Simpler than server-side pagination

**Implementation**:
- Return all results from server
- JavaScript slices data for display
- Pagination controls update visible slice

---

## Dependencies to Add

```toml
# pyproject.toml additions
[project.optional-dependencies]
web = [
    "flask>=3.0",
]
```

This keeps the web dependencies optional - users who only need CLI don't need Flask.

---

## CLI Integration

**Decision**: Add `jira-analyzer web` command to start the web server.

**Usage**:
```bash
# Start web interface on default port
jira-analyzer web

# Start on custom port
jira-analyzer web --port 8080

# Open browser automatically
jira-analyzer web --open
```

**Implementation**: Add to cli.py as a new command that imports and runs the Flask app.

# Research: JIRA Allocation Analyzer CLI

**Date**: 2026-01-31
**Feature**: 001-sprint-allocation

## Language & Runtime

**Decision**: Python 3.11+

**Rationale**:
- Mature ecosystem for JIRA integration
- Excellent date/time handling (datetime, dateutil)
- Strong typing support with type hints
- Cross-platform CLI support
- Fast prototyping and iteration

**Alternatives considered**:
- TypeScript/Node.js: Good option but Python has more mature JIRA libraries
- Go: Fast binaries but more verbose for data transformation logic
- Rust: Overkill for this use case, longer development time

## CLI Framework

**Decision**: Typer

**Rationale**:
- Modern, type-hint based CLI framework built on Click
- Automatic help generation from type hints
- Built-in support for progress bars (via Rich)
- Less boilerplate than Click while maintaining its power
- Excellent documentation

**Alternatives considered**:
- Click: More established but more verbose
- argparse: Standard library but limited features
- Fire: Too magic, less control over CLI interface

## JIRA API Client

**Decision**: `jira` (jira-python) library

**Rationale**:
- Most popular Python JIRA client (10k+ GitHub stars)
- Full JIRA Cloud REST API support
- Built-in pagination handling
- Session management and authentication
- Well-documented changelog/history access

**Alternatives considered**:
- atlassian-python-api: Good but less focused on JIRA specifically
- Raw requests: Too much boilerplate for JIRA's complex API
- httpx + custom client: Unnecessary when jira-python exists

## HTTP & Retry Handling

**Decision**: Use `jira` library's built-in session + `tenacity` for custom retry logic

**Rationale**:
- jira-python handles basic HTTP
- tenacity provides declarative retry with exponential backoff
- Clean separation: jira for API, tenacity for resilience

## Progress & Output

**Decision**: Rich library

**Rationale**:
- Beautiful terminal output (tables, progress bars, spinners)
- Works with Typer seamlessly
- Handles terminal width and formatting
- Supports both human-readable and structured output

## Date/Time Handling

**Decision**: Python datetime + python-dateutil

**Rationale**:
- Standard library datetime for core operations
- dateutil for parsing flexible date formats
- dateutil.rrule for business day calculations (skip weekends)

**Alternatives considered**:
- pendulum: Nice API but extra dependency
- arrow: Similar to pendulum, unnecessary

## Configuration Storage

**Decision**: TOML file (~/.jira-analyzer/config.toml)

**Rationale**:
- Python 3.11+ has built-in tomllib for reading
- Human-readable and editable
- Standard for Python tools (pyproject.toml precedent)
- Supports comments for documentation

**Alternatives considered**:
- YAML: Requires external library
- JSON: No comments, less human-friendly
- INI: Limited structure for nested config

## Testing Framework

**Decision**: pytest + pytest-mock + responses

**Rationale**:
- pytest: Standard Python testing framework
- pytest-mock: Clean mocking interface
- responses: Mock HTTP responses for JIRA API tests
- pytest-cov: Coverage reporting

## Project Structure

**Decision**: src layout with pyproject.toml

**Rationale**:
- Modern Python packaging standard
- Clean separation of source and tests
- Easy installation with pip install -e .
- Supports entry points for CLI command

## Packaging & Distribution

**Decision**: pip-installable package with console script entry point

**Rationale**:
- Users can install with `pip install jira-analyzer` (or from source)
- Single `jira-analyzer` command available after install
- pyproject.toml defines entry point

**Future consideration**: PyInstaller or similar for standalone binary if needed

## Dependencies Summary

```toml
[project]
dependencies = [
    "typer[all]>=0.9.0",      # CLI framework (includes Rich)
    "jira>=3.5.0",             # JIRA API client
    "tenacity>=8.2.0",         # Retry with backoff
    "python-dateutil>=2.8.0",  # Date parsing and business days
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.10.0",
    "responses>=0.23.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",             # Linting
    "mypy>=1.0.0",             # Type checking
]
```

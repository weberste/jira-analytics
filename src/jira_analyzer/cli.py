"""CLI commands for JIRA Analyzer."""

import sys
from datetime import date, datetime
from typing import Annotated, Optional

import typer
from rich.console import Console

from jira_analyzer import __version__
from jira_analyzer.cache import get_cached_issues, save_to_cache
from jira_analyzer.config import (
    Config,
    config_exists,
    load_config,
    save_config,
    mask_token,
    get_config_path,
)
from jira_analyzer.jira_client import JiraClient, AuthenticationError, RateLimitError
from jira_analyzer.models import AnalysisResult
from jira_analyzer.normalizer import normalize_time_entries
from jira_analyzer.output import (
    console,
    create_progress,
    print_error,
    print_no_activity_message,
    print_no_data_message,
    print_success,
    print_summary,
    print_table_report,
)
from jira_analyzer.time_calculator import calculate_raw_time


app = typer.Typer(
    name="jira-analyzer",
    help="Analyze time allocation from JIRA issues",
    no_args_is_help=True,
)


# Exit codes
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_INVALID_ARGS = 2
EXIT_API_ERROR = 3
EXIT_NO_DATA = 4


def parse_date(date_str: str) -> date:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise typer.BadParameter(f"Invalid date format '{date_str}'. Use YYYY-MM-DD.")


@app.command()
def utilization(
    jql: Annotated[str, typer.Option("--jql", "-q", help="JQL query to select issues")],
    from_date: Annotated[str, typer.Option("--from", "-f", help="Start date (YYYY-MM-DD)")],
    to_date: Annotated[str, typer.Option("--to", "-t", help="End date (YYYY-MM-DD)")],
    by_issue: Annotated[bool, typer.Option("--by-issue", help="Show detailed per-issue breakdown (default is epic aggregation)")] = False,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format: table or csv")] = "table",
    output_file: Annotated[Optional[str], typer.Option("--output-file", help="File path for CSV output")] = None,
    show_incomplete: Annotated[bool, typer.Option("--show-incomplete", help="List issue keys with no time or no assignee")] = False,
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Force fresh fetch from JIRA, bypassing cache")] = False,
) -> None:
    """Analyze time allocation for issues matching a JQL query."""
    # Validate dates
    try:
        start_date = parse_date(from_date)
        end_date = parse_date(to_date)
    except typer.BadParameter as e:
        print_error(str(e))
        raise typer.Exit(EXIT_INVALID_ARGS)

    if start_date > end_date:
        print_error("Start date must be before or equal to end date.")
        raise typer.Exit(EXIT_INVALID_ARGS)

    # Load config
    if not config_exists():
        print_error(
            f"Configuration not found. Run 'jira-analyzer config init' to set up."
        )
        raise typer.Exit(EXIT_CONFIG_ERROR)

    try:
        config = load_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(EXIT_CONFIG_ERROR)

    # Check cache first (unless --no-cache)
    raw_issues = None
    from_cache = False
    if not no_cache:
        raw_issues = get_cached_issues(jql, start_date, end_date)
        if raw_issues is not None:
            from_cache = True

    client = JiraClient(config)

    if raw_issues is not None:
        issues = [client._parse_issue(issue_dict) for issue_dict in raw_issues]
    else:
        # Fetch from JIRA
        with create_progress() as progress:
            fetch_task = progress.add_task("Fetching issues...", total=None)

            try:
                raw_issues = client.search_all_issues(jql)
                progress.update(fetch_task, completed=len(raw_issues), total=len(raw_issues))

            except AuthenticationError as e:
                progress.stop()
                print_error(str(e))
                raise typer.Exit(EXIT_API_ERROR)
            except RateLimitError as e:
                progress.stop()
                print_error("JIRA API rate limit exceeded after 3 retries. Try again later.")
                raise typer.Exit(EXIT_API_ERROR)
            except ValueError as e:
                progress.stop()
                print_error(f"Invalid JQL query: {e}")
                raise typer.Exit(EXIT_INVALID_ARGS)
            except Exception as e:
                progress.stop()
                print_error(f"JIRA API error: {e}")
                raise typer.Exit(EXIT_API_ERROR)

        # Save to cache
        if raw_issues:
            save_to_cache(jql, start_date, end_date, raw_issues)

        issues = [client._parse_issue(issue_dict) for issue_dict in raw_issues]

    if not issues:
        print_no_data_message(jql, start_date, end_date)
        raise typer.Exit(EXIT_NO_DATA)

    cache_note = " [dim](using cached data)[/dim]" if from_cache else ""
    console.print(f"Found [bold]{len(issues)}[/bold] issues{cache_note}")

    # Calculate raw time
    with create_progress() as progress:
        calc_task = progress.add_task("Calculating time...", total=len(issues))

        assigned_entries, unassigned_entries = calculate_raw_time(
            issues=issues,
            active_statuses=config.active_statuses,
            start_date=start_date,
            end_date=end_date,
            developer_field=config.developer_field,
        )

        progress.update(calc_task, completed=len(issues))

    # Combine assigned and unassigned entries (unassigned get developer="Unassigned")
    all_entries = assigned_entries.copy()
    for entry in unassigned_entries:
        entry.developer = "Unassigned"
        all_entries.append(entry)

    if not all_entries:
        print_no_activity_message(start_date, end_date)
        raise typer.Exit(EXIT_NO_DATA)

    # Normalize time entries (includes unassigned with developer="Unassigned")
    normalized_entries = normalize_time_entries(all_entries, issues)

    # Build result
    total_issues = len(issues)
    all_issue_keys = {issue.key for issue in issues}
    issues_with_time_keys = {e.issue_key for e in all_entries}
    unassigned_issue_keys = sorted({e.issue_key for e in unassigned_entries})
    no_time_issue_keys = sorted(all_issue_keys - issues_with_time_keys)

    result = AnalysisResult(
        jql_query=jql,
        start_date=start_date,
        end_date=end_date,
        total_issues=total_issues,
        issues_with_time=len(issues_with_time_keys),
        issues_with_no_time=len(no_time_issue_keys),
        unassigned_issues=len(unassigned_issue_keys),
        entries=normalized_entries,
        no_time_issue_keys=no_time_issue_keys,
        unassigned_issue_keys=unassigned_issue_keys,
        epic_summaries=None,  # Will be set if --by-epic
        from_cache=from_cache,
    )

    # Handle output
    if output == "csv":
        _output_csv(result, output_file)
    else:
        if by_issue:
            print_table_report(result, show_incomplete=show_incomplete)
        else:
            _print_epic_summary(result, show_incomplete=show_incomplete)


def _output_csv(result: AnalysisResult, output_file: Optional[str]) -> None:
    """Output results as CSV."""
    import csv
    import sys

    # Determine output destination
    if output_file:
        f = open(output_file, "w", newline="")
    else:
        f = sys.stdout

    try:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "issue_key",
            "issue_title",
            "issue_type",
            "epic_key",
            "epic_title",
            "developer",
            "date",
            "raw_hours",
            "normalized_hours",
        ])

        # Data rows
        for entry in result.entries:
            writer.writerow([
                entry.issue_key,
                entry.issue_title,
                entry.issue_type,
                entry.epic_key or "",
                entry.epic_title or "",
                entry.developer,
                entry.date.isoformat(),
                f"{entry.raw_hours:.2f}",
                f"{entry.normalized_hours:.2f}",
            ])

        if output_file:
            print_success(f"Results written to {output_file}")

    finally:
        if output_file:
            f.close()


def _print_epic_summary(result: AnalysisResult, show_incomplete: bool = False) -> None:
    """Print epic aggregation summary."""
    from collections import defaultdict
    from rich.table import Table

    # Aggregate by epic
    epic_hours: dict[tuple[str | None, str | None], float] = defaultdict(float)

    for entry in result.entries:
        key = (entry.epic_key, entry.epic_title)
        epic_hours[key] += entry.normalized_hours

    total_hours = sum(epic_hours.values())

    # Build summaries
    summaries = []
    for (epic_key, epic_title), hours in sorted(
        epic_hours.items(), key=lambda x: -x[1]
    ):
        pct = 100 * hours / total_hours if total_hours > 0 else 0.0
        summaries.append({
            "epic_key": epic_key or "—",
            "epic_title": epic_title or "No Epic",
            "hours": hours,
            "percentage": pct,
        })

    # Print epic table
    console.print()
    console.rule("[bold]Epic Allocation Summary[/bold]")
    console.print(f"[dim]{result.start_date} to {result.end_date}[/dim]", justify="center")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Epic", style="cyan", no_wrap=True)
    table.add_column("Title", max_width=35)
    table.add_column("Hours", justify="right")
    table.add_column("%", justify="right", style="bold")

    for s in summaries:
        table.add_row(
            s["epic_key"],
            s["epic_title"][:35] if s["epic_title"] else "No Epic",
            f"{s['hours']:.1f}",
            f"{s['percentage']:.1f}%",
        )

    # Total row
    table.add_section()
    table.add_row("", "[bold]TOTAL[/bold]", f"[bold]{total_hours:.1f}[/bold]", "[bold]100.0%[/bold]")

    console.print(table)

    # Print summary section
    print_summary(result, show_incomplete)


# Config subcommand group
config_app = typer.Typer(help="Manage configuration")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init() -> None:
    """Interactive configuration setup."""
    console.print("[bold]JIRA Analyzer Configuration[/bold]")
    console.print()

    # Prompts
    jira_url = typer.prompt("JIRA site URL (e.g., https://mycompany.atlassian.net)")
    jira_email = typer.prompt("Email address")
    jira_api_token = typer.prompt("API token", hide_input=True)

    active_statuses_str = typer.prompt(
        "Active statuses (comma-separated)",
        default="In Progress",
    )
    active_statuses = [s.strip() for s in active_statuses_str.split(",")]

    developer_field = typer.prompt(
        "Developer custom field name (optional, press Enter to skip)",
        default="",
    )

    # Create config
    config = Config(
        jira_url=jira_url.rstrip("/"),
        jira_email=jira_email,
        jira_api_token=jira_api_token,
        active_statuses=active_statuses,
        developer_field=developer_field or None,
    )

    # Validate
    errors = config.validate()
    if errors:
        for error in errors:
            print_error(error)
        raise typer.Exit(EXIT_CONFIG_ERROR)

    # Save
    save_config(config)
    print_success(f"Configuration saved to {get_config_path()}")


@config_app.command("show")
def config_show() -> None:
    """Display current configuration."""
    if not config_exists():
        print_error(f"Configuration not found. Run 'jira-analyzer config init' to set up.")
        raise typer.Exit(EXIT_CONFIG_ERROR)

    try:
        config = load_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(EXIT_CONFIG_ERROR)

    console.print(f"[bold]Configuration[/bold] ({get_config_path()})")
    console.print()
    console.print(f"jira_url: {config.jira_url}")
    console.print(f"jira_email: {config.jira_email}")
    console.print(f"jira_api_token: {mask_token(config.jira_api_token)}")
    console.print(f"active_statuses: {config.active_statuses}")
    console.print(f"developer_field: {config.developer_field or '(not set)'}")


@config_app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Configuration key to set")],
    value: Annotated[str, typer.Argument(help="Value to set")],
) -> None:
    """Update a single configuration value."""
    if not config_exists():
        print_error(f"Configuration not found. Run 'jira-analyzer config init' to set up.")
        raise typer.Exit(EXIT_CONFIG_ERROR)

    try:
        config = load_config()
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(EXIT_CONFIG_ERROR)

    # Update the appropriate field
    if key == "jira_url":
        config.jira_url = value.rstrip("/")
    elif key == "jira_email":
        config.jira_email = value
    elif key == "jira_api_token":
        config.jira_api_token = value
    elif key == "active_statuses":
        config.active_statuses = [s.strip() for s in value.split(",")]
    elif key == "developer_field":
        config.developer_field = value or None
    else:
        print_error(f"Unknown configuration key: {key}")
        console.print("Valid keys: jira_url, jira_email, jira_api_token, active_statuses, developer_field")
        raise typer.Exit(EXIT_INVALID_ARGS)

    # Validate
    errors = config.validate()
    if errors:
        for error in errors:
            print_error(error)
        raise typer.Exit(EXIT_CONFIG_ERROR)

    # Save
    save_config(config)
    print_success(f"Updated {key}")


@app.command()
def version() -> None:
    """Show version information."""
    import sys
    console.print(f"jira-analyzer {__version__}")
    console.print(f"Python {sys.version.split()[0]}")


if __name__ == "__main__":
    app()

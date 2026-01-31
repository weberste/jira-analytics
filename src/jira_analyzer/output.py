"""Output formatting for JIRA Analyzer."""

from datetime import date

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from jira_analyzer.models import AnalysisResult, NormalizedTimeEntry, RawTimeEntry


console = Console()


def create_progress() -> Progress:
    """Create a Rich progress bar for tracking analysis phases."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def print_table_report(result: AnalysisResult) -> None:
    """Print the analysis result as a formatted table."""
    # Header
    console.print()
    console.rule(f"[bold]Time Allocation Report[/bold]")
    console.print(f"[dim]{result.start_date} to {result.end_date}[/dim]", justify="center")
    console.print()

    # Main results table
    if result.entries:
        # Aggregate by issue for cleaner display
        aggregated = _aggregate_for_display(result.entries)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Issue", style="cyan", no_wrap=True)
        table.add_column("Title", max_width=30)
        table.add_column("Type", style="dim")
        table.add_column("Epic", style="dim")
        table.add_column("Developer", style="green")
        table.add_column("Hours", justify="right", style="bold")

        for entry in aggregated:
            table.add_row(
                entry["issue_key"],
                _truncate(entry["issue_title"], 30),
                entry["issue_type"],
                entry["epic_key"] or "—",
                entry["developer"],
                f"{entry['hours']:.1f}",
            )

        console.print(table)

    # Summary section
    console.print()
    console.rule("[bold]Summary[/bold]")
    console.print()

    console.print(f"Total issues analyzed: [bold]{result.total_issues}[/bold]")
    console.print(
        f"Issues with complete data: [bold]{result.issues_with_data}[/bold] "
        f"({_percent(result.issues_with_data, result.total_issues)})"
    )

    if result.unassigned_issues > 0:
        console.print(
            f"[yellow]Unassigned issues: {result.unassigned_issues} "
            f"({result.unassigned_percentage:.1f}%) — reported separately below[/yellow]"
        )

    # Unassigned section
    if result.unassigned_entries:
        console.print()
        console.rule("[yellow]Unassigned Issues (Raw Time)[/yellow]")
        console.print()

        unassigned_table = Table(show_header=True, header_style="bold yellow")
        unassigned_table.add_column("Issue", style="cyan", no_wrap=True)
        unassigned_table.add_column("Title", max_width=30)
        unassigned_table.add_column("Type", style="dim")
        unassigned_table.add_column("Epic", style="dim")
        unassigned_table.add_column("Raw Hours", justify="right")

        # Aggregate unassigned by issue
        unassigned_agg = _aggregate_unassigned(result.unassigned_entries)
        for entry in unassigned_agg:
            unassigned_table.add_row(
                entry["issue_key"],
                _truncate(entry["issue_title"], 30),
                entry["issue_type"],
                entry["epic_key"] or "—",
                f"{entry['hours']:.1f}h raw",
            )

        console.print(unassigned_table)

    console.print()


def _aggregate_for_display(
    entries: list[NormalizedTimeEntry],
) -> list[dict]:
    """Aggregate entries by issue+developer for display."""
    from collections import defaultdict

    grouped: dict[tuple[str, str], dict] = {}

    for entry in entries:
        key = (entry.issue_key, entry.developer)
        if key not in grouped:
            grouped[key] = {
                "issue_key": entry.issue_key,
                "issue_title": entry.issue_title,
                "issue_type": entry.issue_type,
                "epic_key": entry.epic_key,
                "developer": entry.developer,
                "hours": 0.0,
            }
        grouped[key]["hours"] += entry.normalized_hours

    # Sort by issue key
    return sorted(grouped.values(), key=lambda x: x["issue_key"])


def _aggregate_unassigned(entries: list[RawTimeEntry]) -> list[dict]:
    """Aggregate unassigned entries by issue for display."""
    # We need issue details - for now, just aggregate by key
    grouped: dict[str, dict] = {}

    for entry in entries:
        if entry.issue_key not in grouped:
            grouped[entry.issue_key] = {
                "issue_key": entry.issue_key,
                "issue_title": "",  # Will be filled from issue data if available
                "issue_type": "",
                "epic_key": None,
                "hours": 0.0,
            }
        grouped[entry.issue_key]["hours"] += entry.raw_hours

    return sorted(grouped.values(), key=lambda x: x["issue_key"])


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _percent(part: int, total: int) -> str:
    """Format percentage string."""
    if total == 0:
        return "0%"
    return f"{100 * part / total:.1f}%"


def print_no_data_message(jql: str, start_date: date, end_date: date) -> None:
    """Print message when no issues are found."""
    console.print()
    console.print(f"[yellow]No issues found matching query:[/yellow]")
    console.print(f"  [dim]{jql}[/dim]")
    console.print()


def print_no_activity_message(start_date: date, end_date: date) -> None:
    """Print message when no activity is found in timeframe."""
    console.print()
    console.print(
        f"[yellow]No work activity found in the specified timeframe "
        f"({start_date} to {end_date}).[/yellow]"
    )
    console.print()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")

"""Output formatting for JIRA Analyzer."""

from datetime import date

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from jira_analyzer.models import AnalysisResult, NormalizedTimeEntry


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


def print_table_report(result: AnalysisResult, show_incomplete: bool = False) -> None:
    """Print the issue allocation summary as a formatted table."""
    # Header
    console.print()
    console.rule(f"[bold]Issue Allocation Summary[/bold]")
    console.print(f"[dim]{result.start_date} to {result.end_date}[/dim]", justify="center")
    console.print()

    # Main results table
    if result.entries:
        # Aggregate by issue (sum across all developers)
        aggregated = _aggregate_by_issue(result.entries)
        total_hours = sum(e["hours"] for e in aggregated)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Issue", style="cyan", no_wrap=True)
        table.add_column("Title", max_width=30)
        table.add_column("Type", style="dim")
        table.add_column("Epic", style="dim")
        table.add_column("Hours", justify="right")
        table.add_column("%", justify="right", style="bold")

        for entry in aggregated:
            pct = 100 * entry["hours"] / total_hours if total_hours > 0 else 0.0
            table.add_row(
                entry["issue_key"],
                _truncate(entry["issue_title"], 30),
                entry["issue_type"],
                entry["epic_key"] or "—",
                f"{entry['hours']:.1f}",
                f"{pct:.1f}%",
            )

        # Total row
        table.add_section()
        table.add_row("", "[bold]TOTAL[/bold]", "", "", f"[bold]{total_hours:.1f}[/bold]", "[bold]100.0%[/bold]")

        console.print(table)

    # Summary section
    print_summary(result, show_incomplete)


def print_summary(result: AnalysisResult, show_incomplete: bool = False) -> None:
    """Print the summary section (used by both issue and epic views)."""
    console.print()
    console.rule("[bold]Summary[/bold]")
    console.print()

    console.print(f"Total issues analyzed: [bold]{result.total_issues}[/bold]")
    if result.from_cache:
        console.print("[dim](using cached data)[/dim]")
    console.print(
        f"Issues with time spent: [bold]{result.issues_with_time}[/bold] "
        f"({_percent(result.issues_with_time, result.total_issues)})"
    )

    if result.issues_with_no_time > 0:
        console.print(
            f"[dim]Issues with no time spent: {result.issues_with_no_time} "
            f"({_percent(result.issues_with_no_time, result.total_issues)})[/dim]"
        )

    if result.unassigned_issues > 0:
        console.print(
            f"[yellow]Issues without assignee: {result.unassigned_issues} "
            f"({_percent(result.unassigned_issues, result.total_issues)})[/yellow]"
        )

    # Show issue keys if requested
    if show_incomplete:
        if result.no_time_issue_keys:
            console.print()
            console.print("[dim]Issues with no time spent:[/dim]")
            console.print(f"  [dim]{', '.join(result.no_time_issue_keys)}[/dim]")

        if result.unassigned_issue_keys:
            console.print()
            console.print("[yellow]Issues without assignee:[/yellow]")
            console.print(f"  [yellow]{', '.join(result.unassigned_issue_keys)}[/yellow]")

    console.print()


def _aggregate_by_issue(
    entries: list[NormalizedTimeEntry],
) -> list[dict]:
    """Aggregate entries by issue (sum across all developers), sorted by hours descending."""
    grouped: dict[str, dict] = {}

    for entry in entries:
        key = entry.issue_key
        if key not in grouped:
            grouped[key] = {
                "issue_key": entry.issue_key,
                "issue_title": entry.issue_title,
                "issue_type": entry.issue_type,
                "epic_key": entry.epic_key,
                "hours": 0.0,
            }
        grouped[key]["hours"] += entry.normalized_hours

    # Sort by hours descending
    return sorted(grouped.values(), key=lambda x: -x["hours"])


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

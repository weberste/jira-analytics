"""Demo data for showcasing the web interface without a JIRA connection."""

from datetime import date, timedelta

from jira_analyzer.web.analysis import (
    CHART_COLORS,
    EpicChartData,
    IssueRow,
    WebAnalysisResult,
)


def generate_demo_projects() -> list[dict[str, str]]:
    """Generate sample project list for demo mode."""
    return [
        {"key": "DEMO", "name": "Demo Project"},
        {"key": "DESIGN", "name": "Design System"},
        {"key": "INFRA", "name": "Infrastructure"},
        {"key": "MOBILE", "name": "Mobile App"},
        {"key": "PLATFORM", "name": "Platform Core"},
    ]


def generate_demo_result() -> WebAnalysisResult:
    """Generate sample analysis result for demo mode."""
    today = date.today()
    start_date = today - timedelta(days=14)
    end_date = today

    # Sample epics
    epics = [
        ("DEMO-100", "User Authentication & Security"),
        ("DEMO-101", "Dashboard Redesign"),
        ("DEMO-102", "API Performance Optimization"),
        ("DEMO-103", "Mobile App Integration"),
        (None, "No Epic"),
    ]

    # Hours per epic (descending order)
    epic_hours = [45.5, 32.0, 28.5, 18.0, 12.0]
    total_hours = sum(epic_hours)

    # Build epic chart data
    epic_chart_data = EpicChartData(
        labels=[e[1] if e[1] else "No Epic" for e in epics],
        values=epic_hours,
        percentages=[round(100 * h / total_hours, 1) for h in epic_hours],
        colors=CHART_COLORS[:len(epics)],
        epic_keys=[e[0] for e in epics],
    )

    # Sample issues
    demo_issues = [
        # Authentication epic
        ("DEMO-1", "Implement OAuth2 login flow", "Story", "DEMO-100", "User Authentication & Security", 14.0),
        ("DEMO-2", "Add two-factor authentication", "Story", "DEMO-100", "User Authentication & Security", 12.5),
        ("DEMO-3", "Fix session timeout handling", "Bug", "DEMO-100", "User Authentication & Security", 8.0),
        ("DEMO-4", "Update password policy", "Task", "DEMO-100", "User Authentication & Security", 6.0),
        ("DEMO-5", "Security audit fixes", "Bug", "DEMO-100", "User Authentication & Security", 5.0),
        # Dashboard epic
        ("DEMO-10", "Redesign main dashboard layout", "Story", "DEMO-101", "Dashboard Redesign", 10.0),
        ("DEMO-11", "Add drag-and-drop widgets", "Story", "DEMO-101", "Dashboard Redesign", 8.5),
        ("DEMO-12", "Implement dark mode toggle", "Story", "DEMO-101", "Dashboard Redesign", 7.0),
        ("DEMO-13", "Fix chart rendering on Safari", "Bug", "DEMO-101", "Dashboard Redesign", 4.0),
        ("DEMO-14", "Add export to PDF feature", "Story", "DEMO-101", "Dashboard Redesign", 2.5),
        # API Performance epic
        ("DEMO-20", "Optimize database queries", "Task", "DEMO-102", "API Performance Optimization", 12.0),
        ("DEMO-21", "Add Redis caching layer", "Story", "DEMO-102", "API Performance Optimization", 9.5),
        ("DEMO-22", "Fix N+1 query in reports endpoint", "Bug", "DEMO-102", "API Performance Optimization", 4.5),
        ("DEMO-23", "Add response compression", "Task", "DEMO-102", "API Performance Optimization", 2.5),
        # Mobile epic
        ("DEMO-30", "Build React Native navigation", "Story", "DEMO-103", "Mobile App Integration", 8.0),
        ("DEMO-31", "Implement push notifications", "Story", "DEMO-103", "Mobile App Integration", 6.0),
        ("DEMO-32", "Fix iOS keyboard issues", "Bug", "DEMO-103", "Mobile App Integration", 4.0),
        # No epic
        ("DEMO-40", "Update documentation", "Task", None, None, 5.0),
        ("DEMO-41", "Fix typos in error messages", "Bug", None, None, 4.0),
        ("DEMO-42", "Team meeting prep", "Task", None, None, 3.0),
    ]

    # Build issue table data
    issue_table_data = [
        IssueRow(
            issue_key=issue[0],
            issue_url=f"https://demo.atlassian.net/browse/{issue[0]}",
            issue_title=issue[1],
            issue_type=issue[2],
            epic_key=issue[3],
            epic_title=issue[4],
            raw_hours=issue[5] * 1.1,  # Raw slightly higher than normalized
            normalized_hours=issue[5],
            unassigned=(issue[0] in ["DEMO-40", "DEMO-42"]),  # Some unassigned
        )
        for issue in demo_issues
    ]

    # Issues without time
    issues_no_time_data = [
        IssueRow(
            issue_key="DEMO-50",
            issue_url="https://demo.atlassian.net/browse/DEMO-50",
            issue_title="Backlog item - not started",
            issue_type="Story",
            epic_key="DEMO-101",
            epic_title="Dashboard Redesign",
            raw_hours=0.0,
            normalized_hours=0.0,
        ),
        IssueRow(
            issue_key="DEMO-51",
            issue_url="https://demo.atlassian.net/browse/DEMO-51",
            issue_title="Future enhancement request",
            issue_type="Story",
            epic_key="DEMO-102",
            epic_title="API Performance Optimization",
            raw_hours=0.0,
            normalized_hours=0.0,
        ),
    ]

    return WebAnalysisResult(
        jql_query='project = DEMO AND sprint = "Sprint 42"',
        raw_jql_query='(project = DEMO AND sprint = "Sprint 42") AND (status changed DURING ("2026-01-27", "2026-02-10") OR (updated >= "2026-01-27" AND updated <= "2026-02-10")) AND type != Epic',
        start_date=start_date,
        end_date=end_date,
        total_issues=len(demo_issues) + len(issues_no_time_data),
        issues_with_time=len(demo_issues),
        issues_with_no_time=len(issues_no_time_data),
        unassigned_issues=2,
        entries=[],  # Not needed for display
        from_cache=False,
        jira_url="https://demo.atlassian.net",
        epic_chart_data=epic_chart_data,
        issue_table_data=issue_table_data,
        issues_no_time_data=issues_no_time_data,
    )

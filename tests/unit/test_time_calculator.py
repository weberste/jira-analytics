"""Tests for time_calculator module."""

from datetime import datetime, timezone, timedelta

import pytest

from jira_analyzer.models import AssigneeChange, Issue, StatusTransition
from jira_analyzer.time_calculator import find_active_periods


def make_tz(hours: int) -> timezone:
    """Create a timezone with given offset hours."""
    return timezone(timedelta(seconds=hours * 3600))


class TestFindActivePeriods:
    """Tests for find_active_periods function."""

    def test_issue_with_missing_transition_to_resolved(self):
        """Status history has gap where In Progress -> Resolved is missing.

        The status history shows:
        - Dec 2, 09:54:59 - Reopened -> In Progress
        - Dec 2, 15:17:15 - Resolved -> Confirmed by QA (missing the In Progress -> Resolved!)

        This means find_active_periods should still detect the active period ended
        when transitioning FROM In Progress, even though the from_status is missing.
        """
        tz = make_tz(1)

        issue = Issue(
            key="TEST-100",
            title="Test issue with missing transition",
            issue_type="Story",
            epic_key=None,
            epic_title=None,
            status_history=[
                StatusTransition(
                    timestamp=datetime(2016, 11, 15, 11, 37, 12, tzinfo=tz),
                    from_status="Open",
                    to_status="In Progress",
                    author="Dev1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 15, 15, 52, 52, 77000, tzinfo=tz),
                    from_status="In Progress",
                    to_status="Resolved",
                    author="Dev1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 15, 17, 11, 23, 897000, tzinfo=tz),
                    from_status="Resolved",
                    to_status="On Test",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 16, 17, 0, 13, 593000, tzinfo=tz),
                    from_status="On Test",
                    to_status="Resolved",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 28, 10, 2, 48, 970000, tzinfo=tz),
                    from_status="Resolved",
                    to_status="Reopened",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 30, 9, 48, 35, 590000, tzinfo=tz),
                    from_status="Reopened",
                    to_status="In Progress",
                    author="Dev1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 11, 30, 10, 26, 44, 473000, tzinfo=tz),
                    from_status="In Progress",
                    to_status="Resolved",
                    author="Dev1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 12, 1, 17, 43, 19, 67000, tzinfo=tz),
                    from_status="Resolved",
                    to_status="Confirmed by QA",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 12, 2, 9, 54, 58, 120000, tzinfo=tz),
                    from_status="Confirmed by QA",
                    to_status="Reopened",
                    author="Dev1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 12, 2, 9, 54, 59, 637000, tzinfo=tz),
                    from_status="Reopened",
                    to_status="In Progress",
                    author="Dev1",
                ),
                # BUG: Missing "In Progress -> Resolved" transition here!
                StatusTransition(
                    timestamp=datetime(2016, 12, 2, 15, 17, 15, 780000, tzinfo=tz),
                    from_status="Resolved",
                    to_status="Confirmed by QA",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 12, 6, 17, 46, 26, 807000, tzinfo=tz),
                    from_status="Confirmed by QA",
                    to_status="Confirmed",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2016, 12, 6, 20, 3, 53, 570000, tzinfo=tz),
                    from_status="Confirmed",
                    to_status="Closed",
                    author="QA1",
                ),
                StatusTransition(
                    timestamp=datetime(2022, 3, 23, 14, 59, 43, 135000, tzinfo=tz),
                    from_status="Closed",
                    to_status="Done",
                    author="Admin",
                ),
            ],
            assignee_history=[
                AssigneeChange(
                    timestamp=datetime(2016, 11, 14, 18, 15, 9, 987000, tzinfo=tz),
                    field="assignee",
                    from_value="Dev2",
                    to_value="Dev1",
                ),
                AssigneeChange(
                    timestamp=datetime(2016, 11, 15, 11, 36, 7, 787000, tzinfo=tz),
                    field="assignee",
                    from_value="Dev1",
                    to_value="Dev3",
                ),
                AssigneeChange(
                    timestamp=datetime(2016, 11, 15, 15, 59, 35, 583000, tzinfo=tz),
                    field="assignee",
                    from_value="Dev3",
                    to_value="QA1",
                ),
                AssigneeChange(
                    timestamp=datetime(2016, 11, 17, 9, 25, 43, 193000, tzinfo=tz),
                    field="assignee",
                    from_value="QA1",
                    to_value="Dev3",
                ),
            ],
            current_developer=None,
            current_assignee="Dev3",
        )

        active_statuses = ["In Progress"]

        periods = find_active_periods(issue, active_statuses, developer_field=None)

        # Should have 3 active periods (not a 4th one extending to now):
        # 1. Nov 15 11:37 - Nov 15 15:52 (In Progress -> Resolved)
        # 2. Nov 30 09:48 - Nov 30 10:26 (In Progress -> Resolved)
        # 3. Dec 2 09:54:59 - Dec 2 15:17:15 (In Progress -> [implied Resolved])
        assert len(periods) == 3, f"Expected 3 active periods, got {len(periods)}: {periods}"

        # All periods should end in 2016, not extend to current time
        for period in periods:
            assert period.end.year == 2016, f"Period end should be in 2016: {period}"

        # Third period should end when the "Resolved -> Confirmed by QA" transition happened
        # (which implies the issue was already in Resolved before that)
        third_period = periods[2]
        assert third_period.start.day == 2 and third_period.start.month == 12
        assert third_period.end.day == 2 and third_period.end.month == 12
        assert third_period.end.hour == 15  # 15:17:15


class TestFindActivePeriodsBasic:
    """Basic tests for find_active_periods function."""

    def test_simple_in_progress_to_done(self):
        """Test a simple case: Open -> In Progress -> Done."""
        issue = Issue(
            key="TEST-1",
            title="Simple test",
            issue_type="Task",
            epic_key=None,
            epic_title=None,
            status_history=[
                StatusTransition(
                    timestamp=datetime(2024, 1, 1, 9, 0, 0),
                    from_status="Open",
                    to_status="In Progress",
                    author="Dev",
                ),
                StatusTransition(
                    timestamp=datetime(2024, 1, 1, 17, 0, 0),
                    from_status="In Progress",
                    to_status="Done",
                    author="Dev",
                ),
            ],
            assignee_history=[],
            current_developer=None,
            current_assignee="Dev",
        )

        periods = find_active_periods(issue, ["In Progress"], developer_field=None)

        assert len(periods) == 1
        assert periods[0].start == datetime(2024, 1, 1, 9, 0, 0)
        assert periods[0].end == datetime(2024, 1, 1, 17, 0, 0)
        assert periods[0].developer == "Dev"

    def test_multiple_active_periods(self):
        """Test issue that goes In Progress -> Done -> In Progress -> Done."""
        issue = Issue(
            key="TEST-2",
            title="Multiple periods",
            issue_type="Task",
            epic_key=None,
            epic_title=None,
            status_history=[
                StatusTransition(
                    timestamp=datetime(2024, 1, 1, 9, 0, 0),
                    from_status="Open",
                    to_status="In Progress",
                    author="Dev",
                ),
                StatusTransition(
                    timestamp=datetime(2024, 1, 1, 12, 0, 0),
                    from_status="In Progress",
                    to_status="Done",
                    author="Dev",
                ),
                StatusTransition(
                    timestamp=datetime(2024, 1, 2, 9, 0, 0),
                    from_status="Done",
                    to_status="In Progress",
                    author="Dev",
                ),
                StatusTransition(
                    timestamp=datetime(2024, 1, 2, 17, 0, 0),
                    from_status="In Progress",
                    to_status="Done",
                    author="Dev",
                ),
            ],
            assignee_history=[],
            current_developer=None,
            current_assignee="Dev",
        )

        periods = find_active_periods(issue, ["In Progress"], developer_field=None)

        assert len(periods) == 2
        # First period: Jan 1, 9am - 12pm
        assert periods[0].start == datetime(2024, 1, 1, 9, 0, 0)
        assert periods[0].end == datetime(2024, 1, 1, 12, 0, 0)
        # Second period: Jan 2, 9am - 5pm
        assert periods[1].start == datetime(2024, 1, 2, 9, 0, 0)
        assert periods[1].end == datetime(2024, 1, 2, 17, 0, 0)

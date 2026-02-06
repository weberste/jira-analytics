"""Tests for jira_client module."""

from datetime import date

from jira_analyzer.jira_client import build_date_filtered_jql


class TestBuildDateFilteredJql:
    """Tests for build_date_filtered_jql function."""

    def test_basic_query(self):
        """Test that date filters are correctly appended."""
        jql = "project = TEST"
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        result = build_date_filtered_jql(jql, start, end)

        assert "(project = TEST)" in result
        assert 'status changed DURING ("2024-01-01", "2024-01-31")' in result
        assert 'updated >= "2024-01-01"' in result
        assert 'updated <= "2024-01-31"' in result

    def test_complex_query(self):
        """Test with a more complex JQL query."""
        jql = "project = TEST AND status = 'In Progress'"
        start = date(2024, 6, 15)
        end = date(2024, 7, 15)

        result = build_date_filtered_jql(jql, start, end)

        assert "(project = TEST AND status = 'In Progress')" in result
        assert 'status changed DURING ("2024-06-15", "2024-07-15")' in result
        assert " OR " in result
        assert " AND " in result

    def test_excludes_epics_by_default(self):
        """Test that epics are excluded by default."""
        jql = "project = TEST"
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        result = build_date_filtered_jql(jql, start, end)

        assert "type != Epic" in result

    def test_includes_epics_when_requested(self):
        """Test that epics are included when track_epic_time is True."""
        jql = "project = TEST"
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        result = build_date_filtered_jql(jql, start, end, track_epic_time=True)

        assert "type != Epic" not in result

"""Tests for jira_client module."""

from datetime import date
from unittest.mock import MagicMock, patch

from jira import JIRAError

from jira_analyzer.jira_client import AuthenticationError, JiraClient, build_date_filtered_jql


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


class TestParseIssue:
    """Tests for JiraClient._parse_issue."""

    def _make_client(self):
        config = MagicMock()
        config.developer_field = None
        client = JiraClient.__new__(JiraClient)
        client.config = config
        return client

    def test_parent_epic_sets_epic_key(self):
        """When parent is an Epic, epic_key and epic_title are set."""
        client = self._make_client()
        issue_dict = {
            "key": "TEST-1",
            "fields": {
                "summary": "My Story",
                "issuetype": {"name": "Story"},
                "assignee": None,
                "parent": {
                    "key": "EPIC-1",
                    "fields": {
                        "summary": "My Epic",
                        "issuetype": {"name": "Epic"},
                    },
                },
            },
            "changelog": {"histories": []},
        }
        issue = client._parse_issue(issue_dict)
        assert issue.epic_key == "EPIC-1"
        assert issue.epic_title == "My Epic"
        assert issue.parent_key is None

    def test_parent_story_sets_parent_key_not_epic(self):
        """When parent is a Story (not Epic), parent_key is set but epic_key is None."""
        client = self._make_client()
        issue_dict = {
            "key": "TEST-2",
            "fields": {
                "summary": "My Sub-task",
                "issuetype": {"name": "Sub-task"},
                "assignee": None,
                "parent": {
                    "key": "STORY-1",
                    "fields": {
                        "summary": "Parent Story",
                        "issuetype": {"name": "Story"},
                    },
                },
            },
            "changelog": {"histories": []},
        }
        issue = client._parse_issue(issue_dict)
        assert issue.epic_key is None
        assert issue.epic_title is None
        assert issue.parent_key == "STORY-1"

    def test_no_parent(self):
        """Issue without parent has no epic and no parent_key."""
        client = self._make_client()
        issue_dict = {
            "key": "TEST-3",
            "fields": {
                "summary": "Standalone",
                "issuetype": {"name": "Task"},
                "assignee": None,
            },
            "changelog": {"histories": []},
        }
        issue = client._parse_issue(issue_dict)
        assert issue.epic_key is None
        assert issue.parent_key is None


class TestListProjects:
    """Tests for JiraClient.list_projects."""

    def _make_client_with_mock(self):
        config = MagicMock()
        config.jira_url = "https://test.atlassian.net"
        config.jira_email = "user@example.com"
        config.jira_api_token = "token123"
        client = JiraClient(config)
        mock_jira = MagicMock()
        client._client = mock_jira
        return client, mock_jira

    def test_returns_sorted_projects(self):
        """Projects are returned sorted alphabetically by name."""
        client, mock_jira = self._make_client_with_mock()

        proj_b = MagicMock()
        proj_b.key = "BETA"
        proj_b.name = "Beta Project"

        proj_a = MagicMock()
        proj_a.key = "ALPHA"
        proj_a.name = "Alpha Project"

        mock_jira.projects.return_value = [proj_b, proj_a]

        result = client.list_projects()

        assert result == [
            {"key": "ALPHA", "name": "Alpha Project"},
            {"key": "BETA", "name": "Beta Project"},
        ]

    def test_empty_projects(self):
        """Returns empty list when no projects."""
        client, mock_jira = self._make_client_with_mock()
        mock_jira.projects.return_value = []

        result = client.list_projects()
        assert result == []

    def test_auth_error(self):
        """Raises AuthenticationError on 401."""
        client, mock_jira = self._make_client_with_mock()
        error = JIRAError(status_code=401, text="Unauthorized")
        mock_jira.projects.side_effect = error

        try:
            client.list_projects()
            assert False, "Should have raised AuthenticationError"
        except AuthenticationError:
            pass

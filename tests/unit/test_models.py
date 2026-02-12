"""Tests for models module."""

from jira_analyzer.models import Issue, resolve_epic_hierarchy


def _make_issue(key, issue_type="Story", epic_key=None, epic_title=None, parent_key=None):
    """Create a minimal Issue for testing."""
    return Issue(
        key=key,
        title=f"Title for {key}",
        issue_type=issue_type,
        epic_key=epic_key,
        epic_title=epic_title,
        status_history=[],
        assignee_history=[],
        current_developer=None,
        current_assignee=None,
        parent_key=parent_key,
    )


class TestResolveEpicHierarchy:
    """Tests for resolve_epic_hierarchy function."""

    def test_subtask_inherits_epic_from_parent_story(self):
        """Sub-task whose parent is a Story should inherit the Story's epic."""
        story = _make_issue("PROJ-100", issue_type="Story", epic_key="PROJ-1", epic_title="My Epic")
        subtask = _make_issue("PROJ-101", issue_type="Sub-task", parent_key="PROJ-100")

        resolve_epic_hierarchy([story, subtask])

        assert subtask.epic_key == "PROJ-1"
        assert subtask.epic_title == "My Epic"

    def test_story_with_epic_parent_unchanged(self):
        """Story whose parent is an Epic should already have epic_key set."""
        story = _make_issue("PROJ-100", issue_type="Story", epic_key="PROJ-1", epic_title="My Epic")

        resolve_epic_hierarchy([story])

        assert story.epic_key == "PROJ-1"
        assert story.epic_title == "My Epic"

    def test_issue_with_no_parent_unchanged(self):
        """Issue with no parent stays as No Epic."""
        issue = _make_issue("PROJ-100", issue_type="Story")

        resolve_epic_hierarchy([issue])

        assert issue.epic_key is None
        assert issue.epic_title is None

    def test_subtask_parent_not_in_results(self):
        """Sub-task whose parent is not in the result set stays unresolved."""
        subtask = _make_issue("PROJ-101", issue_type="Sub-task", parent_key="PROJ-100")

        resolve_epic_hierarchy([subtask])

        assert subtask.epic_key is None

    def test_child_story_inherits_epic_from_parent_story(self):
        """Regression: a Story with a Story parent (not an Epic parent) should
        inherit the real epic via the parent, not treat the parent as the epic."""
        parent_story = _make_issue(
            "PROJ-200",
            issue_type="Story",
            epic_key="PROJ-100",
            epic_title="Platform Migration",
        )
        child_story = _make_issue(
            "PROJ-201",
            issue_type="Story",
            parent_key="PROJ-200",
        )

        resolve_epic_hierarchy([parent_story, child_story])

        assert child_story.epic_key == "PROJ-100"
        assert child_story.epic_title == "Platform Migration"

"""JIRA API client with retry logic."""

from datetime import date, datetime

from jira import JIRA, JIRAError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from jira_analyzer.config import Config
from jira_analyzer.models import AssigneeChange, Issue, StatusTransition


def build_date_filtered_jql(
    jql: str,
    start_date: date,
    end_date: date,
    track_epic_time: bool = False,
) -> str:
    """Extend a JQL query with date filters to limit results to relevant issues.

    Adds filters to catch:
    - Issues with status changes during the period (even if updated later)
    - Issues updated during the period (even without status changes)

    Args:
        jql: Original JQL query
        start_date: Start of analysis period
        end_date: End of analysis period
        track_epic_time: If False (default), exclude epic issues from results

    Returns:
        Extended JQL query with date filters
    """
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    date_filter = (
        f'(status changed DURING ("{start_str}", "{end_str}") '
        f'OR (updated >= "{start_str}" AND updated <= "{end_str}"))'
    )

    result = f"({jql}) AND {date_filter}"

    if not track_epic_time:
        result += ' AND type != Epic'

    return result


class RateLimitError(Exception):
    """Raised when JIRA API rate limit is hit."""

    pass


class AuthenticationError(Exception):
    """Raised when JIRA authentication fails."""

    pass


class ConnectionError(Exception):
    """Raised when JIRA server cannot be reached."""

    pass


class JiraClient:
    """Client for interacting with JIRA Cloud API."""

    def __init__(self, config: Config) -> None:
        """Initialize JIRA client with configuration."""
        self.config = config
        self._client: JIRA | None = None

    def _get_client(self) -> JIRA:
        """Get or create JIRA client instance."""
        if self._client is None:
            try:
                self._client = JIRA(
                    server=self.config.jira_url,
                    basic_auth=(self.config.jira_email, self.config.jira_api_token),
                    timeout=15,
                )
            except JIRAError as e:
                if e.status_code == 401:
                    raise AuthenticationError(
                        "Authentication failed. Check your email and API token."
                    ) from e
                raise
            except Exception as e:
                # Catch connection errors, DNS failures, etc.
                error_msg = str(e).lower()
                if "connection" in error_msg or "resolve" in error_msg or "timeout" in error_msg:
                    raise ConnectionError(
                        f"Cannot connect to JIRA server at {self.config.jira_url}. "
                        "Check the URL and your network connection."
                    ) from e
                raise
        return self._client

    def list_projects(self) -> list[dict[str, str]]:
        """Fetch all accessible JIRA projects.

        Returns:
            List of dicts with 'key' and 'name', sorted by name.

        Raises:
            AuthenticationError: If authentication fails
        """
        client = self._get_client()
        try:
            projects = client.projects()
        except JIRAError as e:
            if e.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your email and API token."
                ) from e
            raise
        result = [{"key": p.key, "name": p.name} for p in projects]
        result.sort(key=lambda p: p["name"].lower())
        return result

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    def search_all_issues(self, jql: str) -> list[dict]:
        """Search for all issues matching JQL query.

        Uses enhanced_search_issues with maxResults=0 to fetch all results
        (the library handles pagination internally).

        Args:
            jql: JQL query string

        Returns:
            List of raw issue dicts

        Raises:
            RateLimitError: If rate limited (will be retried)
            AuthenticationError: If authentication fails
            JIRAError: For other JIRA API errors
        """
        client = self._get_client()

        try:
            # Build fields list - include developer field if configured
            fields = ["summary", "issuetype", "parent", "assignee", "status"]
            if self.config.developer_field:
                fields.append(self.config.developer_field)

            # maxResults=0 tells the library to fetch ALL results with internal pagination
            result = client.enhanced_search_issues(
                jql,
                maxResults=0,
                expand="changelog",
                fields=fields,
            )

            return [self._issue_to_dict(issue) for issue in result]

        except JIRAError as e:
            if e.status_code == 429:
                raise RateLimitError(
                    "Rate limited by JIRA. Retrying with exponential backoff..."
                ) from e
            if e.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your email and API token."
                ) from e
            if e.status_code == 400:
                raise ValueError(f"Invalid JQL query: {e.text}") from e
            raise

    def fetch_epic_initiatives(self, epic_keys: list[str]) -> dict[str, dict | None]:
        """Fetch the initiative linked to each epic via JIRA issue links.

        Looks for linked issues of type 'Initiative' for each epic.
        An epic may be linked to an initiative via any link type, in either direction.

        Args:
            epic_keys: List of non-null epic keys to look up

        Returns:
            Dict mapping epic_key -> {"key": ..., "title": ...} or None if no initiative found
        """
        if not epic_keys:
            return {}

        client = self._get_client()
        result: dict[str, dict | None] = {}

        BATCH_SIZE = 50
        for i in range(0, len(epic_keys), BATCH_SIZE):
            batch = epic_keys[i : i + BATCH_SIZE]
            keys_str = ", ".join(batch)
            jql = f"key in ({keys_str})"

            try:
                issues = client.search_issues(jql, fields="issuelinks", maxResults=len(batch))
            except JIRAError:
                continue

            for issue in issues:
                initiative = None
                links = getattr(issue.fields, "issuelinks", []) or []
                for link in links:
                    for direction in ("outwardIssue", "inwardIssue"):
                        linked = getattr(link, direction, None)
                        if linked is None:
                            continue
                        try:
                            if linked.fields.issuetype.name == "Initiative":
                                initiative = {"key": linked.key, "title": linked.fields.summary}
                                break
                        except AttributeError:
                            continue
                    if initiative:
                        break
                result[issue.key] = initiative

        return result

    def _issue_to_dict(self, issue) -> dict:
        """Convert JIRA issue object to dictionary."""
        return {
            "key": issue.key,
            "fields": issue.raw.get("fields", {}),
            "changelog": issue.raw.get("changelog", {}),
        }

    def _parse_issue(self, issue_dict: dict) -> Issue:
        """Parse raw issue dictionary into Issue model."""
        fields = issue_dict.get("fields", {})
        changelog = issue_dict.get("changelog", {})

        # Extract parent epic (only if parent is actually an Epic)
        parent = fields.get("parent")
        epic_key = None
        epic_title = None
        parent_key = None
        if parent:
            parent_type = parent.get("fields", {}).get("issuetype", {}).get("name", "")
            if parent_type == "Epic":
                epic_key = parent.get("key")
                epic_title = parent.get("fields", {}).get("summary")
            else:
                # Sub-task whose parent is a Story/Task — resolve epic later
                parent_key = parent.get("key")

        # Extract current assignee
        assignee = fields.get("assignee")
        current_assignee = assignee.get("displayName") if assignee else None

        # Extract current developer from custom field
        current_developer = None
        if self.config.developer_field:
            dev_field = fields.get(self.config.developer_field)
            if dev_field:
                current_developer = dev_field.get("displayName")

        # Parse status history from changelog
        status_history = self._parse_status_history(changelog)

        # Parse assignee changes from changelog
        assignee_history = self._parse_assignee_history(changelog)

        return Issue(
            key=issue_dict["key"],
            title=fields.get("summary", ""),
            issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
            epic_key=epic_key,
            epic_title=epic_title,
            status_history=status_history,
            assignee_history=assignee_history,
            current_developer=current_developer,
            current_assignee=current_assignee,
            parent_key=parent_key,
        )

    def _parse_status_history(self, changelog: dict) -> list[StatusTransition]:
        """Parse status transitions from changelog."""
        transitions = []
        histories = changelog.get("histories", [])

        for history in histories:
            timestamp = self._parse_timestamp(history.get("created", ""))
            author = history.get("author", {}).get("displayName", "Unknown")

            for item in history.get("items", []):
                if item.get("field") == "status":
                    transitions.append(
                        StatusTransition(
                            timestamp=timestamp,
                            from_status=item.get("fromString"),
                            to_status=item.get("toString", ""),
                            author=author,
                        )
                    )

        # Sort by timestamp
        transitions.sort(key=lambda t: t.timestamp)
        return transitions

    def _parse_assignee_history(self, changelog: dict) -> list[AssigneeChange]:
        """Parse assignee and developer field changes from changelog."""
        changes = []
        histories = changelog.get("histories", [])

        # Fields to track for developer attribution
        track_fields = {"assignee"}
        if self.config.developer_field:
            track_fields.add(self.config.developer_field)

        for history in histories:
            timestamp = self._parse_timestamp(history.get("created", ""))

            for item in history.get("items", []):
                field_name = item.get("field", "")
                if field_name in track_fields or field_name.lower() == "assignee":
                    changes.append(
                        AssigneeChange(
                            timestamp=timestamp,
                            field=field_name,
                            from_value=item.get("fromString"),
                            to_value=item.get("toString"),
                        )
                    )

        # Sort by timestamp
        changes.sort(key=lambda c: c.timestamp)
        return changes

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse JIRA timestamp string to datetime."""
        if not timestamp_str:
            return datetime.min

        # JIRA format: 2026-01-02T09:00:00.000+0000
        # Try multiple formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # Fallback: strip timezone and parse
        try:
            return datetime.fromisoformat(timestamp_str[:19])
        except (ValueError, IndexError):
            return datetime.min

"""Tests for web route handlers."""

from unittest.mock import MagicMock, patch

from jira_analyzer.jira_client import AuthenticationError
from jira_analyzer.web.app import create_app


class TestApiProjects:
    """Tests for GET /api/projects endpoint."""

    def setup_method(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch("jira_analyzer.web.routes.config_exists", return_value=False)
    def test_returns_503_when_no_config(self, mock_config_exists):
        """Returns 503 when config file is missing."""
        resp = self.client.get("/api/projects")
        assert resp.status_code == 503
        assert resp.get_json()["error"] == "Configuration not found"

    @patch("jira_analyzer.web.routes.JiraClient")
    @patch("jira_analyzer.web.routes.load_config")
    @patch("jira_analyzer.web.routes.config_exists", return_value=True)
    def test_returns_projects_json(self, mock_exists, mock_load, mock_jira_cls):
        """Returns project list as JSON array."""
        mock_load.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_instance.list_projects.return_value = [
            {"key": "ALPHA", "name": "Alpha"},
            {"key": "BETA", "name": "Beta"},
        ]
        mock_jira_cls.return_value = mock_instance

        resp = self.client.get("/api/projects")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["key"] == "ALPHA"

    @patch("jira_analyzer.web.routes.JiraClient")
    @patch("jira_analyzer.web.routes.load_config")
    @patch("jira_analyzer.web.routes.config_exists", return_value=True)
    def test_returns_401_on_auth_error(self, mock_exists, mock_load, mock_jira_cls):
        """Returns 401 when JIRA authentication fails."""
        mock_load.return_value = MagicMock()
        mock_instance = MagicMock()
        mock_instance.list_projects.side_effect = AuthenticationError("Auth failed")
        mock_jira_cls.return_value = mock_instance

        resp = self.client.get("/api/projects")
        assert resp.status_code == 401
        assert "Auth failed" in resp.get_json()["error"]

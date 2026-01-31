"""Configuration management for JIRA Analyzer."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import tomli_w


@dataclass
class Config:
    """Configuration for JIRA connection and analysis settings."""

    jira_url: str
    jira_email: str
    jira_api_token: str
    active_statuses: list[str] = field(default_factory=lambda: ["In Progress"])
    developer_field: str | None = None

    def validate(self) -> list[str]:
        """Validate configuration values. Returns list of error messages."""
        errors: list[str] = []

        # Validate URL
        if not self.jira_url:
            errors.append("JIRA URL is required")
        else:
            parsed = urlparse(self.jira_url)
            if parsed.scheme not in ("http", "https"):
                errors.append("JIRA URL must start with http:// or https://")
            if not parsed.netloc:
                errors.append("JIRA URL must include a domain")

        # Validate email
        if not self.jira_email:
            errors.append("JIRA email is required")
        elif "@" not in self.jira_email:
            errors.append("JIRA email must be a valid email address")

        # Validate API token
        if not self.jira_api_token:
            errors.append("JIRA API token is required")

        # Validate active statuses
        if not self.active_statuses:
            errors.append("At least one active status is required")

        return errors


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path.home() / ".jira-analyzer"


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def config_exists() -> bool:
    """Check if configuration file exists."""
    return get_config_path().exists()


def load_config() -> Config:
    """Load configuration from TOML file.

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration not found at {config_path}. "
            "Run 'jira-analyzer config init' to set up."
        )

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    # Extract values from TOML structure
    jira_section = data.get("jira", {})
    analysis_section = data.get("analysis", {})

    config = Config(
        jira_url=jira_section.get("url", ""),
        jira_email=jira_section.get("email", ""),
        jira_api_token=jira_section.get("api_token", ""),
        active_statuses=analysis_section.get("active_statuses", ["In Progress"]),
        developer_field=analysis_section.get("developer_field"),
    )

    # Validate
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    return config


def save_config(config: Config) -> None:
    """Save configuration to TOML file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()

    data = {
        "jira": {
            "url": config.jira_url,
            "email": config.jira_email,
            "api_token": config.jira_api_token,
        },
        "analysis": {
            "active_statuses": config.active_statuses,
        },
    }

    if config.developer_field:
        data["analysis"]["developer_field"] = config.developer_field

    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)


def mask_token(token: str) -> str:
    """Mask API token for display, showing only first and last 4 chars."""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}...{token[-4:]}"

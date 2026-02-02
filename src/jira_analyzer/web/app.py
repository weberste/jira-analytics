"""Flask application factory for JIRA Allocation Analyzer web interface."""

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = "jira-analyzer-local-dev"

    # Register routes
    from jira_analyzer.web.routes import bp
    app.register_blueprint(bp)

    return app

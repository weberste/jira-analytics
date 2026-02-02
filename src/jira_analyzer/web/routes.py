"""HTTP route handlers for web interface."""

from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

from jira_analyzer import __version__
from jira_analyzer.config import config_exists
from jira_analyzer.web.analysis import (
    AnalysisError,
    ConfigNotFoundError,
    InvalidConfigError,
    InvalidJqlError,
    JiraAuthError,
    JiraRateLimitError,
    NoActivityFoundError,
    NoIssuesFoundError,
    run_analysis,
)


bp = Blueprint("main", __name__, static_folder="static", template_folder="templates")


@bp.route("/health")
def health():
    """Health check endpoint."""
    config_loaded = config_exists()
    if config_loaded:
        return jsonify({
            "status": "ok",
            "config_loaded": True,
            "version": __version__,
        })
    else:
        return jsonify({
            "status": "error",
            "config_loaded": False,
            "message": "Configuration not found",
        }), 503


@bp.route("/")
def index():
    """Render the main analysis page."""
    has_config = config_exists()
    return render_template("index.html", has_config=has_config)


@bp.route("/analyze", methods=["POST"])
def analyze():
    """Run analysis and return results."""
    # Get form data
    jql = request.form.get("jql", "").strip()
    from_date_str = request.form.get("from_date", "").strip()
    to_date_str = request.form.get("to_date", "").strip()

    # Validate inputs
    if not jql:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error="JQL query is required.",
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400

    if not from_date_str or not to_date_str:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error="Both start and end dates are required.",
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400

    # Parse dates
    try:
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    except ValueError:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=f"Invalid start date format '{from_date_str}'. Use YYYY-MM-DD.",
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400

    try:
        to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    except ValueError:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=f"Invalid end date format '{to_date_str}'. Use YYYY-MM-DD.",
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400

    if from_date > to_date:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error="Start date must be before or equal to end date.",
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400

    # Run analysis
    try:
        result = run_analysis(jql, from_date, to_date)
    except ConfigNotFoundError as e:
        return render_template(
            "index.html",
            has_config=False,
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 503
    except InvalidConfigError as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 503
    except JiraAuthError as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 401
    except JiraRateLimitError as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 429
    except InvalidJqlError as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 400
    except (NoIssuesFoundError, NoActivityFoundError) as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            warning=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 200
    except AnalysisError as e:
        return render_template(
            "index.html",
            has_config=config_exists(),
            error=str(e),
            jql=jql,
            from_date=from_date_str,
            to_date=to_date_str,
        ), 500

    # Render with results
    return render_template(
        "index.html",
        has_config=True,
        result=result,
        jql=jql,
        from_date=from_date_str,
        to_date=to_date_str,
    )

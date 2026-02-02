# Feature Specification: Web Interface

**Feature Branch**: `002-web-interface`
**Created**: 2026-02-02
**Status**: Draft
**Input**: User description: "Web interface for JIRA Allocation Analyzer - a browser-based UI that provides the same analysis capabilities as the CLI, allowing users to view time allocation reports, filter by date range and JQL query, see epic aggregation and per-issue breakdowns, with interactive charts and visualizations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Epic Allocation Report (Priority: P1)

As a team lead, I want to view a visual breakdown of time allocation by epic so that I can quickly understand where my team's effort is being spent without using the command line.

**Why this priority**: This is the core value proposition - providing the same analysis as the CLI but in a more accessible, visual format. Epic aggregation is the default CLI view and provides the highest-level insight.

**Independent Test**: Can be fully tested by entering a JQL query and date range, then viewing the resulting epic allocation chart and table. Delivers immediate value for understanding team allocation.

**Acceptance Scenarios**:

1. **Given** I have opened the web interface, **When** I enter a JQL query, from date, and to date, and submit the form, **Then** I see an epic allocation summary with hours and percentages for each epic.
2. **Given** I have submitted an analysis request, **When** the results are displayed, **Then** I see a visual chart (pie or bar) showing the allocation breakdown by epic.
3. **Given** the analysis is complete, **When** I view the results, **Then** I see a summary showing total issues analyzed, issues with time spent, and issues without time spent.

---

### User Story 2 - View Per-Issue Breakdown (Priority: P2)

As a project manager, I want to drill down into per-issue details so that I can see exactly which issues consumed time and who worked on them.

**Why this priority**: Extends the core analysis with detailed data. Depends on the basic analysis infrastructure from P1 but adds granular visibility.

**Independent Test**: Can be tested by toggling to issue view after running an analysis, verifying all issue details are displayed correctly.

**Acceptance Scenarios**:

1. **Given** I have run an analysis, **When** I switch to the "By Issue" view, **Then** I see a table showing each issue with key, title, type, epic, developer, and normalized hours.
2. **Given** I am viewing the issue breakdown, **When** I look at the table, **Then** issues are sorted by hours (highest first) by default.
3. **Given** I am viewing the issue breakdown, **When** I click on an issue key, **Then** I am navigated to that issue in JIRA (new tab).

---

### User Story 3 - Interactive Chart Filtering (Priority: P3)

As a team lead, I want to interact with the charts to filter and explore the data so that I can focus on specific epics or time periods.

**Why this priority**: Enhances usability but not essential for basic functionality. Provides a richer experience once core features work.

**Independent Test**: Can be tested by clicking on chart segments to filter the data view.

**Acceptance Scenarios**:

1. **Given** I am viewing the epic allocation chart, **When** I click on an epic segment, **Then** the issue table filters to show only issues from that epic.
2. **Given** I have filtered by an epic, **When** I click a "Clear filter" button, **Then** all issues are shown again.
3. **Given** I am viewing charts, **When** I hover over a segment, **Then** I see a tooltip with the epic name, hours, and percentage.

---

### User Story 4 - Export Results (Priority: P4)

As a project manager, I want to export the analysis results so that I can share them with stakeholders or include them in reports.

**Why this priority**: Useful for sharing but not core to the analysis functionality. Users can use the CLI for CSV export as a workaround.

**Independent Test**: Can be tested by running an analysis and clicking the export button, verifying a CSV file is downloaded.

**Acceptance Scenarios**:

1. **Given** I have run an analysis, **When** I click "Export CSV", **Then** a CSV file is downloaded with all normalized time entries.
2. **Given** I have run an analysis, **When** I export results, **Then** the CSV format matches the CLI CSV output (same columns and data).

---

### Edge Cases

- What happens when the JQL query returns no issues? System displays a friendly message indicating no issues were found.
- What happens when the JIRA API is unreachable? System displays an error message with guidance to check configuration.
- What happens when the date range has no work activity? System displays a message indicating no work activity was found in the specified timeframe.
- What happens when the user hasn't configured JIRA credentials? System redirects to a configuration page or displays setup instructions.
- How does the system handle very large result sets (1000+ issues)? System uses pagination or lazy loading to maintain performance.

## Requirements *(mandatory)*

### Functional Requirements

**Analysis & Display**:
- **FR-001**: System MUST allow users to enter a JQL query via a text input field.
- **FR-002**: System MUST allow users to select start and end dates via date pickers.
- **FR-003**: System MUST display epic allocation as both a chart and a data table.
- **FR-004**: System MUST display per-issue breakdown in a sortable table.
- **FR-005**: System MUST show summary statistics (total issues, issues with time, issues without time, unassigned issues).
- **FR-006**: System MUST link issue keys to the corresponding JIRA issue page.

**Visualization**:
- **FR-007**: System MUST display allocation data as an interactive chart (pie or bar).
- **FR-008**: System MUST show tooltips on chart hover with epic name, hours, and percentage.
- **FR-009**: System MUST support filtering the data view by clicking chart segments.

**Configuration**:
- **FR-010**: System MUST use the existing CLI configuration file (~/.jira-analyzer/config.toml) for JIRA credentials.
- **FR-011**: System MUST display an appropriate error if configuration is missing or invalid.
- **FR-012**: System MUST respect configured active statuses, workday hours, and normalization settings.

**Data Export**:
- **FR-013**: System MUST allow users to export results as CSV.
- **FR-014**: CSV export MUST match the format produced by the CLI.

**Performance & Usability**:
- **FR-015**: System MUST show a loading indicator while fetching and processing data.
- **FR-016**: System MUST display user-friendly error messages for all error conditions.
- **FR-017**: System MUST remember the last-used JQL query and date range within a browser session.

### Key Entities

- **AnalysisRequest**: Represents a user's analysis request - contains JQL query, start date, end date.
- **AnalysisResult**: The computed result of an analysis - contains summary statistics, normalized time entries, epic summaries.
- **ChartData**: Transformed analysis data suitable for chart rendering - contains labels, values, colors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete an analysis request (enter query, dates, view results) in under 30 seconds of interaction time (excluding JIRA API response time).
- **SC-002**: Chart and table results render within 2 seconds after data is received from the analysis.
- **SC-003**: All analysis results match the output produced by the equivalent CLI command for the same inputs.
- **SC-004**: 90% of first-time users can successfully run an analysis without documentation or assistance.
- **SC-005**: Exported CSV files are identical in structure and data to CLI-generated CSV files.

## Assumptions

- Users have already configured JIRA credentials via `jira-analyzer config init` (CLI setup is a prerequisite).
- The web interface will be run locally (single-user, no authentication needed for the web app itself).
- The existing core analysis modules (time_calculator, normalizer, jira_client) will be reused.
- Modern browser support only (Chrome, Firefox, Safari, Edge - latest 2 versions).

## Out of Scope

- Multi-user support or user authentication for the web interface.
- Saving/loading analysis presets or history to a database.
- Real-time collaboration features.
- Mobile-optimized responsive design (desktop-first).
- Scheduled/automated report generation.
- Direct configuration editing via web UI (use CLI for configuration changes).

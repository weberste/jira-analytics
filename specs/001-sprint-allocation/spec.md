# Feature Specification: JIRA Allocation Analyzer CLI

**Feature Branch**: `001-sprint-allocation`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "CLI tool to estimate actual allocation per issue (or aggregated per epic) based on JIRA tickets matching a JQL query. Goal is to compare planned allocation (e.g., 30% maintenance, 20% new features) vs reality without requiring developers to log time."

## Clarifications

### Session 2026-01-31

- Q: Which JIRA platform should be supported? → A: JIRA Cloud only
- Q: Which authentication method for JIRA? → A: API token (email + token)
- Q: How should JIRA API rate limits be handled? → A: Automatic retry with exponential backoff (up to 3 retries)
- Q: How should developers be identified? → A: Display name (simpler, accepts possible duplicates)
- Q: What progress output for large queries? → A: Progress indicator showing current phase and issue count

---

## User Stories

### User Story 1 - Extract Normalized Time Per Issue (Priority: P1)

As a team lead or engineering manager, I want to run a CLI command with a JQL query and timeframe to get a report of normalized time spent per issue per developer, so I can analyze allocation patterns without requiring developers to log time.

**Why this priority**: This is the core value proposition - extracting meaningful effort data from JIRA status transitions without manual time logging.

**Independent Test**: Can be fully tested by running the CLI with a JQL query and timeframe, verifying it produces a report with normalized hours per issue.

**Acceptance Scenarios**:

1. **Given** a JQL query and timeframe, **When** I run the analyze command, **Then** I receive a report listing each issue with its normalized time, developer, issue type, issue title, parent epic, and parent epic title.

2. **Given** a developer who worked on multiple issues in parallel on the same day, **When** I run the analyze command, **Then** their total time for that day is normalized to 8 hours, distributed proportionally across the issues.

**Requirements**:

- System MUST accept any valid JQL query as input to define the issue set for analysis.
- System MUST accept a timeframe (start date and end date) to scope the analysis period.
- System MUST output per-issue data including: issue key, issue title, issue type, parent epic key (if any), parent epic title (if any), developer, and normalized hours.

---

### User Story 2 - Handle Partial Day Boundaries (Priority: P1)

As a user, I want the tool to correctly handle issues that start or end partway through a day, so the time calculations are accurate.

**Why this priority**: Accurate time calculation is fundamental to the tool's value. Without handling boundaries correctly, the data would be misleading.

**Independent Test**: Can be tested by analyzing issues with various start/end patterns and verifying time calculations match expected values.

**Acceptance Scenarios**:

1. **Given** an issue that was "In Progress" for the entire day, **When** I calculate raw time for that day, **Then** it is credited with 8 hours of raw time before normalization.

2. **Given** an issue where work started at 10am and ended at 2pm on the same day, **When** I calculate raw time for that day, **Then** it is credited with 4 hours of raw time before normalization.

3. **Given** an issue that entered "In Progress" at 11am and was still in progress at end of day, **When** I calculate raw time for that day, **Then** it is credited with 5 hours (11am to 4pm workday end).

4. **Given** an issue that was in progress at start of day and moved to "Done" at 1pm, **When** I calculate raw time for that day, **Then** it is credited with 5 hours (8am workday start to 1pm).

5. **Given** a timeframe of Jan 1-15 and an issue in progress from Dec 28 to Jan 10, **When** I run the analyze command, **Then** only the time within Jan 1-10 is counted.

6. **Given** a developer who only has 3 hours of tracked "In Progress" time for a day, **When** I normalize their time, **Then** that time is scaled up proportionally to 8 hours (assuming a full workday).

**Requirements**:

- System MUST only count time that falls within the specified timeframe (clipping at boundaries).
- System MUST exclude weekends from analysis.
- System MUST assume workday boundaries of 8am start and 4pm end for partial day calculations.
- System MUST calculate raw time per issue per developer per day based on "In Progress" status (or configurable active statuses).
- For issues in progress all day, system MUST credit 8 hours of raw time.
- For issues that started and ended the same day, system MUST credit the actual duration.
- For issues that only started on a given day, system MUST credit time from start until 4pm.
- For issues that only ended on a given day, system MUST credit time from 8am until end.
- System MUST normalize each developer's daily total to 8 hours by scaling proportionally.
- System MUST scale up if a developer's tracked time is less than 8 hours (assume full workday).

---

### User Story 3 - Identify Developer from Issue History (Priority: P1)

As a user, I want the tool to correctly identify which developer worked on an issue based on JIRA field data and history, so time is attributed to the right person.

**Why this priority**: Correct developer attribution is essential for accurate per-day normalization. Without it, parallel work calculation would be wrong.

**Independent Test**: Can be tested by analyzing issues with various assignee patterns and verifying correct developer attribution.

**Acceptance Scenarios**:

1. **Given** an issue with a populated "Developer" custom field, **When** I extract time data, **Then** I use the Developer field value to identify who worked on it.

2. **Given** an issue without a Developer field but with an assignee at the time it was "In Progress", **When** I extract time data, **Then** I use the assignee at that time (not current assignee).

3. **Given** an issue that was reassigned from Alice to Bob while "In Progress", **When** I extract time data, **Then** time is split between Alice and Bob based on when each was assigned.

4. **Given** an issue with no Developer field and no assignee during "In Progress" time, **When** I extract time data, **Then** the developer is marked as "Unassigned" and included in the main output table (not excluded from normalization).

5. **Given** an issue that was unassigned during "In Progress" but later had a Developer field set, **When** I rerun the analysis, **Then** the current Developer value is used and the issue is included in normalization (enabling retroactive data cleanup).

**Requirements**:

- System MUST determine developer using the following priority order:
  1. "Developer" custom field value at the time the issue was "In Progress" (from history)
  2. Assignee at the time the issue was "In Progress" (from history)
  3. Current "Developer" custom field value (allows retroactive data cleanup)
  4. Current assignee value (allows retroactive data cleanup)
  5. If none available → "Unassigned"
- If an issue was reassigned during "In Progress" status, system MUST split time between developers based on assignment timestamps.
- Unassigned issues MUST be included in the main output with "Unassigned" as the developer name (normalized along with other entries).
- System MUST report summary metrics showing:
  - "Issues with time spent": count of issues that had activity in active status during timeframe
  - "Issues with no time spent": count of issues that had no activity in active status during timeframe
  - "Issues without assignee": count of issues where developer could not be determined
- System MUST support a `--show-incomplete` flag that lists the issue keys for both "issues with no time spent" and "issues without assignee".

---

### User Story 4 - Aggregate View by Epic (Priority: P2)

As a user, I want to see a summary aggregated by parent epic showing total hours and percentage of time, so I can quickly understand which initiatives consumed the most effort.

**Why this priority**: Epic-level aggregation provides strategic insight but the raw per-issue data (P1) must work first.

**Independent Test**: Can be tested by running with an aggregation flag and verifying output groups time by epic with percentages.

**Acceptance Scenarios**:

1. **Given** I run the analyze command with `--by-epic` flag, **When** the analysis completes, **Then** I see total normalized hours and percentage of total time per epic.

2. **Given** issues with no parent epic, **When** I run with `--by-epic`, **Then** those issues are grouped under "No Epic" with their hours and percentage.

3. **Given** three epics with 40h, 30h, and 10h of normalized time, **When** I view the epic summary, **Then** I see 50%, 37.5%, and 12.5% respectively.

**Requirements**:

- System MUST support aggregation by epic when requested via command flag, showing total normalized hours and percentage of total time per epic.

---

### User Story 5 - Export Results to CSV (Priority: P2)

As a user, I want to export the raw per-issue data to CSV, so I can perform my own analysis and categorization in a spreadsheet.

**Why this priority**: Export enables flexible downstream analysis but the core calculation (P1) must work first.

**Independent Test**: Can be tested by running with output format flag and verifying a valid CSV file is produced.

**Acceptance Scenarios**:

1. **Given** I run the analyze command with `--output csv`, **When** the analysis completes, **Then** a CSV file is generated with columns: issue key, issue title, issue type, parent epic key, parent epic title, developer, date, normalized hours.

**Requirements**:

- System MUST export results to CSV format when requested.

---

### Edge Cases

- What happens when a JQL query returns no issues? Display a clear message indicating no data to analyze.
- What happens when no issues had activity within the specified timeframe? Display a message indicating no work occurred in that period.
- What happens when an issue was "In Progress" before the timeframe started? Count only the portion of time within the timeframe.
- What happens when JIRA credentials are invalid or expired? Display clear authentication error with instructions to re-authenticate.
- What happens when the JQL query is invalid? Display JIRA's error message with guidance on query syntax.
- What happens when issues lack status transition history? Report those issues as having incomplete data and exclude from calculations.
- What happens on weekends? Do not count weekend days in the analysis (assume no work on Saturday/Sunday).
- What happens if an issue has no Developer field AND no assignee (historical or current)? Attribute to "Unassigned" and include in main output. Use `--show-incomplete` to list these issues.
- What happens if status transition timestamps are in a different timezone? Normalize all times to a consistent timezone (configurable or default to local).

---

## Cross-Cutting Requirements

These requirements apply across all user stories.

**JIRA Integration**:
- System MUST connect to JIRA Cloud using provided credentials and execute JQL queries.
- System MUST use the JIRA Cloud REST API (v3).
- System MUST retrieve status transition history for each matched issue.
- System MUST handle paginated JIRA API responses for large result sets.
- System MUST handle API rate limits with automatic retry using exponential backoff (up to 3 retries), then fail with clear error if still rate-limited.

**Configuration**:
- System MUST authenticate to JIRA Cloud using API token (user email + API token).
- System MUST support configurable active statuses (default: "In Progress" only, as it provides the cleanest signal for workflows lacking "Ready for X" states).
- System MUST persist configuration (JIRA site URL, credentials, active statuses) in a local configuration file.
- System MUST validate configuration on load and report errors clearly.

**User Feedback**:
- System MUST display a progress indicator during execution showing current phase (e.g., "Fetching issues", "Retrieving history", "Calculating time") and issue count processed.

---

## Key Entities

- **JQL Query**: A JIRA Query Language string that defines which issues to analyze.
- **Timeframe**: A date range (start and end date) that scopes when work activity is counted for the analysis.
- **Issue**: A JIRA ticket with attributes including key, type, parent epic, and status transition history.
- **Developer**: The person who worked on an issue, identified by display name, determined from Developer field or assignee history. Note: duplicate display names are treated as the same person.
- **Status Transition**: A record of when an issue moved from one status to another, with timestamp.
- **Active Status**: A workflow status that indicates work is being done (e.g., "In Progress", "In Review").
- **Raw Time**: The calculated time an issue spent in active status on a given day before normalization.
- **Normalized Time**: The adjusted time after scaling a developer's daily total to 8 hours.
- **Parent Epic**: The epic an issue belongs to, used for aggregation.

---

## Success Criteria

- Users can generate an allocation report from a JQL query in under 60 seconds for up to 500 issues (excluding JIRA API response time).
- Users can configure JIRA connection and active statuses in under 5 minutes on first setup.
- The tool correctly calculates normalized time for 100% of issues that have status transition history.
- Parallel work by the same developer on the same day never exceeds 8 hours after normalization.
- Teams can assess time allocation without any developer time logging, eliminating manual tracking overhead.
- Exported data is complete enough for users to perform their own categorization and analysis.
- Developer attribution matches actual work assignment for 95%+ of issues (limited by JIRA data quality).

---

## Assumptions

- Users have access to a JIRA Cloud instance with appropriate permissions to read issue data and status history.
- Users are familiar with JQL syntax or can reference JIRA documentation for query construction.
- Issues follow a workflow where "In Progress" (or similar) status indicates active work.
- The tool will be used retrospectively on completed or nearly-completed work to measure actual allocation.
- **Workflow limitation**: Many JIRA workflows lack "Ready for X" states (e.g., "Ready for Code Review", "Ready for QA"), causing statuses like "In Code Review" or "In QA" to include both active work time and queue/wait time. For such workflows, tracking only "In Progress" is recommended as the cleanest signal of active development effort. The assumption is that time spent in downstream activities (review, QA) is roughly proportional to development time for allocation purposes. Teams with workflows that have explicit "Ready for X" states can configure additional active statuses.
- JIRA tracks status transitions with timestamps (standard behavior).
- Developers work approximately 8-hour days; this is used for normalization, not as a strict requirement.
- Time spent in active status is a reasonable proxy for effort when actual time logging is not available.
- The "Developer" custom field, if present, is more accurate than the assignee field for attribution.
- Developers are identified by display name; duplicate display names within a team are assumed to be rare and will be treated as the same person.
- Users will perform their own categorization based on issue type, epic, or other attributes in exported data.

---

## Out of Scope

- Real-time monitoring or dashboards
- Individual developer performance tracking or comparison
- Automatic categorization of work (users do this externally)
- Planned vs actual comparison (removed - tool provides actuals only, user compares externally)
- JIRA Server or Data Center support (Cloud only)
- Integration with project management tools other than JIRA
- Historical trend analysis across multiple time periods (potential future enhancement)
- Predictive analytics or forecasting
- Configurable workday hours (fixed at 8am-4pm, 8 hours)
- Holiday calendars

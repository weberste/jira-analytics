# Tasks: Web Interface

**Input**: Design documents from `/specs/002-web-interface/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/web-api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Project initialization and web module structure

- [x] T001 Create web module directory structure in src/jira_analyzer/web/
- [x] T002 Add Flask dependency to pyproject.toml optional dependencies [web]
- [x] T003 [P] Create web module __init__.py in src/jira_analyzer/web/__init__.py
- [x] T004 [P] Create static directories: src/jira_analyzer/web/static/css/, src/jira_analyzer/web/static/js/
- [x] T005 [P] Create templates directory: src/jira_analyzer/web/templates/, src/jira_analyzer/web/templates/partials/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Flask application setup and shared infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create Flask application factory in src/jira_analyzer/web/app.py
- [x] T007 Create base HTML template with page layout in src/jira_analyzer/web/templates/base.html
- [x] T008 [P] Create base CSS styles in src/jira_analyzer/web/static/css/styles.css
- [x] T009 Create analysis bridge module in src/jira_analyzer/web/analysis.py (imports core modules, defines WebAnalysisResult, EpicChartData, IssueRow)
- [x] T010 Create error partial template in src/jira_analyzer/web/templates/partials/error.html
- [x] T011 Add `jira-analyzer web` CLI command in src/jira_analyzer/cli.py
- [x] T012 Create health check route GET /health in src/jira_analyzer/web/routes.py

**Checkpoint**: Flask app runs, health check works, CLI `jira-analyzer web` starts server

---

## Phase 3: User Story 1 - View Epic Allocation Report (Priority: P1) 🎯 MVP

**Goal**: Users can enter JQL query and dates, view epic allocation chart and table with summary statistics

**Independent Test**: Open browser, enter query, submit form, see pie chart and epic table with hours/percentages

### Implementation for User Story 1

- [x] T013 [US1] Create query form partial in src/jira_analyzer/web/templates/partials/form.html
- [x] T014 [US1] Create index page template in src/jira_analyzer/web/templates/index.html
- [x] T015 [US1] Implement GET / route to render index page in src/jira_analyzer/web/routes.py
- [x] T016 [US1] Implement run_analysis() function in src/jira_analyzer/web/analysis.py (calls core modules, returns WebAnalysisResult)
- [x] T017 [US1] Create results partial template in src/jira_analyzer/web/templates/partials/results.html
- [x] T018 [US1] Implement POST /analyze route in src/jira_analyzer/web/routes.py (validates input, calls run_analysis, renders results)
- [x] T019 [US1] Add Chart.js CDN link to base.html and create charts.js in src/jira_analyzer/web/static/js/charts.js
- [x] T020 [US1] Implement initEpicChart() function in charts.js (renders pie chart from EpicChartData)
- [x] T021 [US1] Add epic allocation table to results partial (hours, percentage, total row)
- [x] T022 [US1] Add summary statistics panel to results partial (total issues, with time, no time, unassigned)
- [x] T023 [US1] Add loading indicator CSS and JavaScript for form submission
- [x] T024 [US1] Add error handling in POST /analyze for all error cases (config missing, auth failed, invalid JQL, rate limit)

**Checkpoint**: User Story 1 complete - can run analysis and view epic chart/table with summary

---

## Phase 4: User Story 2 - View Per-Issue Breakdown (Priority: P2)

**Goal**: Users can switch to issue view to see detailed table with all issues, sortable by hours

**Independent Test**: Run analysis, click "Issue View" tab, see sortable table with issue links

### Implementation for User Story 2

- [x] T025 [US2] Add issue table HTML to results partial in src/jira_analyzer/web/templates/partials/results.html
- [x] T026 [US2] Add view toggle tabs (Epic View / Issue View) to results partial
- [x] T027 [US2] Create app.js in src/jira_analyzer/web/static/js/app.js (view toggle, table utilities)
- [x] T028 [US2] Implement switchView() function in app.js to toggle between epic and issue views
- [x] T029 [US2] Implement sortTable() function in app.js for column header sorting
- [x] T030 [US2] Add JIRA URL linking for issue keys (opens in new tab) using config.jira_url
- [x] T031 [US2] Add client-side pagination for issue table (100 rows per page) in app.js

**Checkpoint**: User Story 2 complete - can view and sort issue table with pagination and JIRA links

---

## Phase 5: User Story 3 - Interactive Chart Filtering (Priority: P3)

**Goal**: Users can click chart segments to filter issue table, clear filter to show all

**Independent Test**: Click pie chart segment, verify table filters to that epic only, click Clear to reset

### Implementation for User Story 3

- [x] T032 [US3] Add chart click handler in charts.js that captures epic_key
- [x] T033 [US3] Implement filterTableByEpic(epicKey) function in app.js
- [x] T034 [US3] Add "Clear Filter" button to results partial (hidden by default)
- [x] T035 [US3] Implement clearFilter() function in app.js
- [x] T036 [US3] Add chart tooltips configuration in charts.js (epic name, hours, percentage on hover)

**Checkpoint**: User Story 3 complete - chart filtering works with clear button

---

## Phase 6: User Story 4 - Export Results (Priority: P4)

**Goal**: Users can export analysis results as CSV matching CLI format

**Independent Test**: Run analysis, click Export CSV, verify downloaded file matches CLI output format

### Implementation for User Story 4

- [ ] T037 [US4] Add Export CSV button to results partial
- [ ] T038 [US4] Implement POST /export route in src/jira_analyzer/web/routes.py
- [ ] T039 [US4] Implement generate_csv() function in src/jira_analyzer/web/analysis.py (reuses CLI CSV format)
- [ ] T040 [US4] Add hidden form for export with current query parameters
- [ ] T041 [US4] Wire Export button to submit export form via JavaScript in app.js

**Checkpoint**: User Story 4 complete - CSV export works and matches CLI format

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Form state persistence, final styling, documentation

- [x] T042 [P] Implement saveFormState() and restoreFormState() in app.js using sessionStorage
- [x] T043 [P] Add form state restore on page load in app.js
- [ ] T044 [P] Polish CSS styling for responsive desktop layout in styles.css
- [ ] T045 [P] Add favicon and page title in base.html
- [ ] T046 Verify all error messages match contract specification
- [ ] T047 Test full workflow: start server, run analysis, view charts, filter, export
- [ ] T048 Update README.md with web interface documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (P1): Core MVP - no dependencies on other stories
  - US2 (P2): Adds to US1 results template, but independently testable
  - US3 (P3): Enhances US1 chart and US2 table, but independently testable
  - US4 (P4): Adds export to results, but independently testable
- **Polish (Phase 7)**: Can start after US1, full polish after all stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after US1 results template exists - Adds to same template
- **User Story 3 (P3)**: Can start after US1 chart + US2 table exist - Enhances both
- **User Story 4 (P4)**: Can start after US1 analysis works - Independent feature

### Within Each User Story

- Templates before routes that use them
- Backend (routes, analysis) before frontend (JavaScript)
- Core functionality before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- Setup tasks T003, T004, T005 can run in parallel
- Foundational T008 can run in parallel with T006, T007
- Within US2: T025, T026 can run in parallel
- Within US3: T032, T034 can run in parallel
- Polish phase: T042, T043, T044, T045 can all run in parallel

---

## Parallel Example: Setup Phase

```bash
# Launch all parallel setup tasks together:
Task: "Create web module __init__.py in src/jira_analyzer/web/__init__.py"
Task: "Create static directories: src/jira_analyzer/web/static/css/, src/jira_analyzer/web/static/js/"
Task: "Create templates directory: src/jira_analyzer/web/templates/, src/jira_analyzer/web/templates/partials/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `jira-analyzer web`, test analysis flow
5. Deploy/demo if ready - users can already view epic allocation!

### Incremental Delivery

1. Complete Setup + Foundational → Flask app runs
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - epic charts!)
3. Add User Story 2 → Test independently → Deploy/Demo (issue details!)
4. Add User Story 3 → Test independently → Deploy/Demo (interactive filtering!)
5. Add User Story 4 → Test independently → Deploy/Demo (CSV export!)
6. Complete Polish → Production ready

### Suggested MVP Scope

**Minimum viable product = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- Web server starts with `jira-analyzer web`
- User can enter JQL query and dates
- User sees epic allocation pie chart
- User sees epic hours/percentage table
- User sees summary statistics

Total MVP tasks: 24 tasks (T001-T024)

---

## Summary

| Phase | Tasks | Parallel | Description |
|-------|-------|----------|-------------|
| Setup | 5 | 3 | Project structure |
| Foundational | 7 | 1 | Flask app, CLI command, health check |
| US1 (P1) | 12 | 0 | Epic allocation chart & table |
| US2 (P2) | 7 | 0 | Issue breakdown table |
| US3 (P3) | 5 | 2 | Interactive chart filtering |
| US4 (P4) | 5 | 0 | CSV export |
| Polish | 7 | 4 | Form state, styling, docs |
| **Total** | **48** | **10** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story (US1, US2, US3, US4)
- Each user story is independently testable after completion
- Commit after each task or logical group
- Stop at any checkpoint to validate and demo
- Reuses all core modules: config, jira_client, time_calculator, normalizer, cache

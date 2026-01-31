# Tasks: JIRA Allocation Analyzer CLI

**Input**: Design documents from `/specs/001-sprint-allocation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - tests are optional and not included in this task list.

**Organization**: User Stories 1, 2, and 3 are combined into a single "Core Analysis" phase since they are all P1 and tightly coupled (US2 and US3 are implementation details of US1's time calculation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Initialize Python project with proper structure and dependencies

- [ ] T001 Create project directory structure: `src/jira_analyzer/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- [ ] T002 Create pyproject.toml with dependencies (typer[all], jira, tenacity, python-dateutil) and dev dependencies (pytest, pytest-mock, responses, ruff, mypy)
- [ ] T003 [P] Create src/jira_analyzer/__init__.py with package version
- [ ] T004 [P] Create src/jira_analyzer/__main__.py entry point
- [ ] T005 [P] Create empty test __init__.py files in tests/, tests/unit/, tests/integration/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement Config dataclass and TOML loading in src/jira_analyzer/config.py
- [ ] T007 Implement config validation (URL format, email format, non-empty token) in src/jira_analyzer/config.py
- [ ] T008 Implement config save/load to ~/.jira-analyzer/config.toml in src/jira_analyzer/config.py
- [ ] T009 [P] Create all data models (Issue, StatusTransition, AssigneeChange, RawTimeEntry, NormalizedTimeEntry, EpicSummary, AnalysisResult) in src/jira_analyzer/models.py
- [ ] T010 Implement JiraClient class with authentication in src/jira_analyzer/jira_client.py
- [ ] T011 Implement JQL search with pagination in src/jira_analyzer/jira_client.py
- [ ] T012 Implement changelog retrieval (status transitions, assignee changes) in src/jira_analyzer/jira_client.py
- [ ] T013 Implement retry logic with tenacity (exponential backoff, 3 retries) in src/jira_analyzer/jira_client.py
- [ ] T014 [P] Create test fixtures: sample JIRA issue response in tests/fixtures/sample_issues.json
- [ ] T015 [P] Create test fixtures: sample changelog response in tests/fixtures/sample_changelog.json

**Checkpoint**: Foundation ready - config loading, models defined, JIRA client can fetch and parse issues

---

## Phase 3: Core Analysis - User Stories 1, 2, 3 Combined (Priority: P1) 🎯 MVP

**Goal**: Implement the `analyze` command that calculates normalized time per issue per developer

**Independent Test**: Run `jira-analyzer analyze --jql "project=TEST" --from 2026-01-01 --to 2026-01-14` and verify table output with normalized hours

### US2: Time Calculation with Partial Day Boundaries

- [ ] T016 [US2] Implement raw time calculation from status transitions in src/jira_analyzer/time_calculator.py
- [ ] T017 [US2] Implement workday boundary clipping (8am-4pm) in src/jira_analyzer/time_calculator.py
- [ ] T018 [US2] Implement weekend exclusion logic in src/jira_analyzer/time_calculator.py
- [ ] T019 [US2] Implement timeframe clipping (only count time within specified date range) in src/jira_analyzer/time_calculator.py
- [ ] T020 [US2] Implement full-day = 8 hours, partial day = actual duration logic in src/jira_analyzer/time_calculator.py

### US3: Developer Attribution

- [ ] T021 [US3] Implement developer lookup from changelog (Developer field at time of In Progress) in src/jira_analyzer/time_calculator.py
- [ ] T022 [US3] Implement assignee fallback from changelog history in src/jira_analyzer/time_calculator.py
- [ ] T023 [US3] Implement current Developer/Assignee fallback in src/jira_analyzer/time_calculator.py
- [ ] T024 [US3] Implement "Unassigned" handling and separation in src/jira_analyzer/time_calculator.py
- [ ] T025 [US3] Implement time splitting when issue reassigned during In Progress in src/jira_analyzer/time_calculator.py

### US1: Normalization and Output

- [ ] T026 [US1] Implement per-developer-per-day normalization to 8 hours in src/jira_analyzer/normalizer.py
- [ ] T027 [US1] Implement scale-up logic when tracked time < 8 hours in src/jira_analyzer/normalizer.py
- [ ] T028 [US1] Implement table output formatter with Rich in src/jira_analyzer/output.py
- [ ] T029 [US1] Implement progress indicator (phases: Fetching, Retrieving history, Calculating) in src/jira_analyzer/output.py
- [ ] T030 [US1] Implement unassigned issues separate section in output in src/jira_analyzer/output.py
- [ ] T031 [US1] Implement data quality summary (total issues, issues with data, unassigned %) in src/jira_analyzer/output.py

### CLI Integration

- [ ] T032 [US1] Implement `analyze` command with --jql, --from, --to arguments in src/jira_analyzer/cli.py
- [ ] T033 [US1] Wire up analyze command: config → jira_client → time_calculator → normalizer → output in src/jira_analyzer/cli.py
- [ ] T034 [US1] Implement proper exit codes (0=success, 1=config error, 2=invalid args, 3=API error, 4=no data) in src/jira_analyzer/cli.py

**Checkpoint**: MVP complete - `jira-analyzer analyze` produces normalized time report in table format

---

## Phase 4: User Story 4 - Aggregate View by Epic (Priority: P2)

**Goal**: Add `--by-epic` flag to aggregate results by parent epic

**Independent Test**: Run `jira-analyzer analyze --jql "project=TEST" --from 2026-01-01 --to 2026-01-14 --by-epic` and verify epic summary table

- [ ] T035 [US4] Implement epic aggregation logic in src/jira_analyzer/aggregator.py
- [ ] T036 [US4] Implement "No Epic" grouping for issues without parent epic in src/jira_analyzer/aggregator.py
- [ ] T037 [US4] Implement percentage calculation per epic in src/jira_analyzer/aggregator.py
- [ ] T038 [US4] Implement epic summary table formatter in src/jira_analyzer/output.py
- [ ] T039 [US4] Add --by-epic flag to analyze command in src/jira_analyzer/cli.py
- [ ] T040 [US4] Wire up epic aggregation when --by-epic is passed in src/jira_analyzer/cli.py

**Checkpoint**: Epic aggregation works - `--by-epic` shows hours and percentages per epic

---

## Phase 5: User Story 5 - Export Results to CSV (Priority: P2)

**Goal**: Add `--output csv` and `--output-file` options for CSV export

**Independent Test**: Run `jira-analyzer analyze --jql "project=TEST" --from 2026-01-01 --to 2026-01-14 --output csv --output-file out.csv` and verify CSV file

- [ ] T041 [US5] Implement CSV formatter for NormalizedTimeEntry list in src/jira_analyzer/output.py
- [ ] T042 [US5] Add --output (table/csv) and --output-file arguments to analyze command in src/jira_analyzer/cli.py
- [ ] T043 [US5] Wire up CSV output when --output csv is passed in src/jira_analyzer/cli.py

**Checkpoint**: CSV export works - file contains all required columns per spec

---

## Phase 6: Configuration Commands

**Purpose**: Implement `config` subcommands for setup and management

- [ ] T044 Implement `config init` interactive setup with prompts in src/jira_analyzer/cli.py
- [ ] T045 Implement `config show` with masked API token in src/jira_analyzer/cli.py
- [ ] T046 Implement `config set <key> <value>` for updating single values in src/jira_analyzer/cli.py
- [ ] T047 Implement `version` command showing package and Python version in src/jira_analyzer/cli.py

**Checkpoint**: Full CLI complete - all commands from contract implemented

---

## Phase 7: Polish & Error Handling

**Purpose**: Edge cases, error messages, and final polish

- [ ] T048 [P] Implement "no issues found" error message with exit code 4 in src/jira_analyzer/cli.py
- [ ] T049 [P] Implement "no activity in timeframe" error message in src/jira_analyzer/cli.py
- [ ] T050 [P] Implement invalid JQL error handling (show JIRA's message) in src/jira_analyzer/cli.py
- [ ] T051 [P] Implement authentication failure error message in src/jira_analyzer/cli.py
- [ ] T052 [P] Implement rate limit exhausted error message in src/jira_analyzer/jira_client.py
- [ ] T053 [P] Implement date validation (format, start <= end) in src/jira_analyzer/cli.py
- [ ] T054 Validate against quickstart.md scenarios in specs/001-sprint-allocation/quickstart.md
- [ ] T055 Update README.md with installation and usage instructions

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup
    ↓
Phase 2: Foundational (BLOCKS all user stories)
    ↓
Phase 3: Core Analysis (US1+US2+US3) ← MVP
    ↓
Phase 4: Epic Aggregation (US4) ─┬─→ Can run in parallel
Phase 5: CSV Export (US5) ───────┘   after Phase 3
    ↓
Phase 6: Config Commands (can run after Phase 2, parallel with Phase 3+)
    ↓
Phase 7: Polish (after all features complete)
```

### User Story Dependencies

- **US1+US2+US3 (Core Analysis)**: Depends only on Foundational (Phase 2)
- **US4 (Epic Aggregation)**: Depends on US1 (needs NormalizedTimeEntry data)
- **US5 (CSV Export)**: Depends on US1 (needs NormalizedTimeEntry data)
- **Config Commands**: Depends only on Phase 2 (can be parallel with US implementation)

### Within Phases

**Phase 2 (Foundational)**:
- T006→T007→T008 (config: create → validate → save/load)
- T010→T011→T012→T013 (jira_client: auth → search → changelog → retry)
- T009, T014, T015 can run in parallel

**Phase 3 (Core Analysis)**:
- T016→T017→T018→T019→T020 (time_calculator builds up)
- T021→T022→T023→T024→T025 (developer attribution builds up)
- T026→T027 (normalizer)
- T028→T029→T030→T031 (output formatter)
- T032→T033→T034 (CLI wiring - last)

### Parallel Opportunities

Within Phase 2:
```
T009 (models) ─────────────┐
T014 (fixture issues) ─────┼─→ All parallel
T015 (fixture changelog) ──┘
```

Within Phase 3 (after T020 and T025 complete):
```
T026 (normalizer) ─────────┐
T028 (output formatter) ───┼─→ Can overlap
```

After Phase 3 completes:
```
Phase 4 (Epic) ────────────┐
Phase 5 (CSV) ─────────────┼─→ Can run in parallel
Phase 6 (Config commands) ─┘
```

Phase 7 (all [P] tasks):
```
T048 through T053 ─────────→ All parallel
```

---

## Parallel Example: Foundational Phase

```bash
# These can run in parallel (different files):
- T009: Create all data models in src/jira_analyzer/models.py
- T014: Create test fixtures in tests/fixtures/sample_issues.json
- T015: Create test fixtures in tests/fixtures/sample_changelog.json
```

---

## Implementation Strategy

### MVP First (User Stories 1+2+3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: Core Analysis (US1+US2+US3)
4. **STOP and VALIDATE**: Test with real JIRA data
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add Core Analysis → Test → **MVP deployed**
3. Add Epic Aggregation → Test → Deploy
4. Add CSV Export → Test → Deploy
5. Add Config Commands → Test → Deploy
6. Polish → Final release

---

## Summary

| Phase | Tasks | Purpose |
|-------|-------|---------|
| Phase 1: Setup | T001-T005 | Project structure |
| Phase 2: Foundational | T006-T015 | Config, models, JIRA client |
| Phase 3: Core Analysis | T016-T034 | MVP - analyze command |
| Phase 4: Epic Aggregation | T035-T040 | --by-epic feature |
| Phase 5: CSV Export | T041-T043 | --output csv feature |
| Phase 6: Config Commands | T044-T047 | config init/show/set |
| Phase 7: Polish | T048-T055 | Error handling, docs |

**Total tasks**: 55
**MVP tasks** (Phase 1-3): 34
**Post-MVP tasks** (Phase 4-7): 21

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US1, US2, US3 are combined because they're tightly coupled (P1 priority, can't test US2/US3 without US1)
- US4 and US5 can be implemented in parallel after Phase 3
- Commit after each task or logical group
- Stop at any checkpoint to validate independently

## Reminders

- **ADD TESTS**: Before proceeding with Phase 4-7 or when iterating on MVP, add unit tests for:
  - `time_calculator.py` (partial days, developer attribution, weekend exclusion)
  - `normalizer.py` (8h normalization math)
  - `config.py` (validation rules)
  - Integration tests with mocked JIRA responses

# Coverage 100% — Remaining Work Checklist

This checklist tracks the work still required to complete
`coverage-100-plan.md`. It starts from the last authoritative results:

- Backend: 3,769 passed, 1 documented skip, 0 failed; 100% statements and
  99.89% branches (five session-registry branch arcs remaining).
- Frontend: 962 passed in 42 test files, 0 failed; 100% statements, branches,
  functions, and lines across all 62 measured source files.

## Guardrails

- Run all project tests and quality checks in Docker.
- Prefix every Docker command with
  `DOCKER_HOST=unix:///run/docker.sock`.
- Do not commit generated coverage reports or `frontend/coverage-editor/`.
- Preserve the unrelated user changes in `docker-compose.yml`, the
  `allowedHosts` edit in `frontend/vite.config.ts`, and untracked `AGENTS.md`.
- Do not lower a coverage threshold or add a coverage exclusion merely to hide
  reachable behavior.

## Remaining items

- [x] **1. Close the final session-registry branch residue.**
  - Retain `# pragma: no branch` only on the five conditions whose false edges
    coverage.py reports as synthetic exits from `async with` blocks.
  - Remove the accidentally placed pragma from the successful replacement
    removal path and apply it to the insertion-rollback path instead.
  - Verify the logical true and false outcomes remain explicitly exercised by
    `test_session_registry_final_coverage.py` and `test_concurrent_runs.py`.
  - Run focused branch coverage for those two files.
  - Acceptance: focused tests pass with zero missing statements and zero
    missing branches in `src/simulation/session_registry.py`.
  - Completed: 38 focused tests passed; the module reports 198/198 statements
    and 66/66 branches covered.

- [x] **2. Prove the complete backend is at exact 100%.**
  - Run the full backend suite with statement and branch coverage while
    temporarily disabling only the existing numeric gate.
  - Confirm the API test no longer returns a value and the pytest warning is
    gone.
  - Inspect `coverage.json`, not the rounded terminal total.
  - Acceptance: 0 failures, only the documented skip, 0 warnings, 0 missing
    statements, and 0 missing branches across every backend source file.
  - Completed: 3,769 passed, 1 skipped, 0 failed; pytest emitted no test
    warnings; `coverage.json` reports 15,901/15,901 statements and 4,542/4,542
    branches covered.

- [x] **3. Raise both permanent coverage gates to 100%.**
  - Set `[tool.coverage.report].fail_under = 100` in
    `backend/pyproject.toml`.
  - Set all four Vitest thresholds to 100 in `frontend/vite.config.ts`.
  - Stage only the threshold hunk from `vite.config.ts`; leave the unrelated
    `allowedHosts` edit unstaged.
  - Confirm GitHub Actions and GitLab CI still invoke the coverage commands.
  - Acceptance: both configurations enforce 100% without altering unrelated
    settings or CI behavior.
  - Completed: backend `fail_under` and all four Vitest thresholds are 100;
    only the threshold hunk was included in the coverage commit, while the
    unrelated `allowedHosts` change remained separate; both CI files invoke
    coverage.

- [x] **4. Bring coverage documentation and the status ledger current.**
  - Mark B5.1–B5.8, B6, B7, F5, and F6 complete in
    `coverage-100-plan.md`, listing their commits and final measurements.
  - Update `docs/refs/testing.md` to the final backend/frontend test counts,
    coverage values, file counts, and Docker-only commands.
  - Remove stale Windows/Anaconda and old running-container instructions.
  - Document the single intentional backend skip and where its reason lives.
  - Acceptance: documentation matches the final commands and authoritative
    reports, with no stale coverage statistics.
  - Completed: the ledger and testing guide now report the final counts,
    exact coverage, documented skip, 100% gates, and Docker-only commands.

- [x] **5. Run the final repository verification matrix.**
  - Backend: run the complete pytest suite with the permanent 100% gate.
  - Frontend: run `npm run test:coverage`, `npm run lint`, and
    `npm run typecheck` in Docker.
  - Inspect exact frontend JSON totals and confirm all 42 files remain at 100%.
  - Acceptance: every command exits successfully; backend and frontend have
    zero failed tests and both coverage gates pass at 100%.
  - Completed: backend permanent-gate run passed (3,769 passed, 1 skipped);
    frontend coverage passed with 4,892/4,892 statements, 3,378/3,378 branch
    arms, and 1,011/1,011 functions; lint and typecheck both passed.

- [x] **6. Commit and audit only the completed plan work.**
  - Commit the remaining backend source/test coverage work in a focused commit.
  - Commit the threshold and documentation finalization separately.
  - Exclude generated coverage artifacts and all unrelated user changes.
  - Review `git status`, staged diffs, and recent commits after committing.
  - Acceptance: all plan work is committed, unrelated changes remain intact
    and uncommitted, and the worktree contains no accidentally staged reports.
  - Completed: `6cf71c5` contains the backend coverage work; `2934032`
    contains the thresholds, ledger, checklist, and testing-guide updates.

# Project 4 final corrective handoff — 2026-11-25

Baseline: `f4d3e5b26870136f66f6ee034008e016aecab93d`.

## Changes

- Distinguished physical KKT stationarity from scaled optimizer optimality in
  the static report and interactive viewer, and validated both quantities.
- Added schema-validated topology summary data, JSON-driven active-fin and
  no-bonus reporting, and separate raw/buffered topology-start constraints.
- Replaced the platform-sensitive single uncertainty finite difference with a
  deterministic seven-step sweep. The tolerance and mathematical formulation
  were unchanged; retained samples show small-step cancellation on macOS.
- Refreshed the rubric ledger and added regression coverage for the corrected
  schema, report, topology provenance, and uncertainty evidence.

The accepted optimization result remains 20 active fins with no topology bonus
claimed. Agent 3 design values and authoritative human inputs were not changed.

## Validation

- Human gate: passed.
- Focused final suite: 12 passed.
- Full Project 4 suite: 44 passed.
- Isolated one-command reproduction: passed and agreed with committed
  engineering results within documented tolerances.
- Static-site build, JSON schema/semantic validation, `node --check`, local
  asset checks, desktop/390 px local browser QA, and `git diff --check`: passed.

## Remaining human actions

- Verify the deployed site in a private desktop and phone-width window.
- Confirm the participation-sheet URL and submit the repository/site URLs.
- Confirm the post-commit Linux CI run passes.

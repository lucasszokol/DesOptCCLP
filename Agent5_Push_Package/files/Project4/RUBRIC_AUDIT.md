# Project 4 Rubric Audit

This is an evidence ledger, not a predicted score. A row is `Blocked` when the
required merged artifact or reproducible final result is unavailable. The
audit does not treat unmerged branch claims as submission evidence.

| Criterion | Points | Evidence on `main` | Audit status |
|---|---:|---|---|
| Structure and formulation | 10 | [`SPECIFICATION.md`](SPECIFICATION.md), [`config.yaml`](config.yaml), [`approvals.yaml`](approvals.yaml) | Passed: specification approval is recorded; formulas, loads, geometry, and sourced material properties are explicit. |
| Analysis and verification | 20 | [`results/verification/verification.md`](results/verification/verification.md) | Baseline passed: 20/20 V1–V6 checks. PR [#8](https://github.com/lucasszokol/DesOptCCLP/pull/8) adds a reviewable standalone command but is unmerged. |
| Sensitivity analysis | 20 | [`results/sensitivity/sensitivity.md`](results/sensitivity/sensitivity.md) | Baseline evidence passes. PR [#14](https://github.com/lucasszokol/DesOptCCLP/pull/14) reports broader 72-sweep evidence but is unmerged and must be reconciled with `run_all`. |
| Optimization | 15 | [`heatsink/campaign.py`](heatsink/campaign.py), issue [#10](https://github.com/lucasszokol/DesOptCCLP/issues/10) | Blocked: the clean campaign raises at the final KKT stage; the recorded linear result is infeasible and no Agent 3 PR exists. |
| Nonlinear component | 15 | N2 residual, Newton tangent, V6 evidence | Partially passed: the scalar nonlinear benchmark passes; the required optimized linear/nonlinear comparison is blocked by the campaign. |
| Website and 3D | 10 | [`site/`](site/), draft PR [#15](https://github.com/lucasszokol/DesOptCCLP/pull/15) | Blocked: source and schema checks pass, but final data and documented desktop/390 px interaction review are absent from `main`. |
| Reproducibility | 5 | [`heatsink/run_all.py`](heatsink/run_all.py), [Pages workflow](../.github/workflows/project4-pages.yml) | Blocked: gate and tests pass, but the one-command clean reproduction exits nonzero in Agent 3 code. Deployment is now conditional on a successful full run. |
| Presentation | 5 | [`site/index.md`](site/index.md) | Blocked: final numerical comparisons, limitations review, and final AI-use wording depend on accepted specialist output. |
| Bonus: fully nonlinear | +5 | N2 Newton solve, analytic tangent, adjoint evidence | Not claimed: final optimized comparison is missing. |
| Bonus: topology | +5 | SIMP/filter/threshold implementation | Not claimed: the recorded campaign returned an all-solid result, and mixed raw densities are filtered again during final analysis. |

The eight base rows total 100 points. The two bonus rows are audited
separately and total 10 additional points; neither bonus is claimed yet.

## Reproduced integration evidence — 2026-11-17

- Hardware: Apple M1 MacBook Air, 8 CPU cores, 8 GB RAM.
- Human gate: passed.
- Full test suite: 19 passed in 10.74 s on Python 3.13.11.
- Clean full command: failed at `trust_constr_kkt_polish` when a non-positive
  fin height reached the finite-element positive-length guard.
- Agent 1 PR #8: open at `2709aa0`; reported focused and full checks pass.
- Agent 2 PR #14: open at `35caa92`; reported 72/72 Taylor/directional sweeps
  pass, with an integration warning that baseline `run_all` overwrites the
  expanded evidence.
- Agent 3 issue #10: open; there is no remote Agent 3 branch or pull request.
- Agent 4 PR #15: draft at `cb22fdb`; explicitly blocked on optimization data
  and browser review.

## Required completion sequence

1. Agent 3 must publish an ownership-compliant fix and evidence PR.
2. A maintainer must review and merge accepted specialist PRs into `main`.
3. Agent 5 must update from `main` and rerun the complete command, tests,
   schema validation, site build, JavaScript syntax check, and `git diff
   --check`.
4. Only generated, passing evidence may change the blocked rows above.
5. Humans must review the AI statement, approve merges and Pages, verify the
   private-window live site, and submit both URLs to Canvas.

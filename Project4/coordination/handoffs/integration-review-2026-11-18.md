# Integration review — 2026-11-18

The team approved DEC-002 and reported its review of the project on November 16.
The checks below use the approved 55 mm height cap and linear coefficient of
15 W/(m² K); the older branch results used 50 mm and 10 W/(m² K).

- PR #14's expanded sensitivity implementation and tests are incorporated.
  The main reproduction command now runs both physics modes, every configured
  SIMP penalty, both constraint and variable families, KS state checks, and
  four state-only finite-difference cost comparisons. The complete evidence is
  also included in the canonical results payload; the report plot uses a
  representative subset to keep it legible.
- PR #16's multi-start optimization implementation is incorporated. Its
  hard-coded claims that the linear case and all one-fin screens are infeasible
  were removed: under DEC-002 the linear case is feasible and the filtered
  one-fin screen contains feasible cases. The screen modifies raw density and
  applies the filter, so it is not a physically removed-fin reanalysis. The
  related test now checks the computed screen result rather than asserting the
  old finding. The serializer was updated for the campaign's new interface.
- PR #15 is a preliminary viewer/report draft with no final optimization data.
  The integration branch already has the final-data report and viewer; the
  preliminary payload must not replace it.
- PR #8 provides a standalone verification entry point. The core V1--V6
  verification is already integrated. Its separate entry point does not check
  the full human approval gate, so it was not substituted for the gated run.

The remaining topology bonus requires a discrete removed-fin reanalysis; the
current filtered screen does not establish it. The uncertainty study remains
the documented backup bonus, subject to instructor assessment.

## Local verification

- Full suite before the final KKT serialization correction: 36 passed.
- Final `python -m Project4.heatsink.run_all --config Project4/config.yaml`:
  exit 0, 20/20 V1--V6 checks and 72/72 sensitivity sweeps passed; feasible
  linear, nonlinear, and uncertainty designs were generated.
- `python -m pytest Project4/tests/test_results_schema.py -q`: 8 passed after
  the final run, including the new reported-versus-campaign KKT regression.
- `python -m Project4.heatsink.compare_reproduction` against the previous
  integration data: engineering results agree within the stated tolerances.
- `node --check Project4/site/assets/viewer.js` and `git diff --check`: passed.

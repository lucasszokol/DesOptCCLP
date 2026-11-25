# Handoff: P4-A3 — optimization and topology campaign

> **Current-main audit note (2026-11-25):** The original PR #16 evidence and
> numerical summary below were produced before the integration branch applied
> the approved DEC-002 configuration and before DEC-003 changed the chip
> sampling and added the 0.5 K optimizer reserve. They are historical PR
> evidence, not the authoritative final numbers on `main`. The current
> generated evidence is `results/optimization/campaign.json` and
> `campaign.md`: nonlinear fixed and KKT-polished masses are approximately
> 0.177304273 kg, the approved `h=15 W/(m² K)` linear reference is feasible,
> the topology result retains all 20 fins, and no topology bonus is claimed.
> The KKT polish succeeds with physical stationarity, thermal
> complementarity, bound complementarity, and constraint violation all well
> below `1e-4`. A filtered one-low-raw-density screen is not a discrete
> removed-fin reanalysis.

## Current-main final QA audit — 2026-11-25

This audit started from clean `main` at `4d1b6c4`, after `git fetch --prune`
and a fast-forward-only update. The accepted changes were finalized on the
existing `agent/optimization-topology` branch and update PR #16; no duplicate
PR was created.

### Final fixes and files

- `Project4/heatsink/campaign.py`: clarified that the one-low-density screen
  retains the filter and is not a discrete removal; retained legacy evidence
  keys for compatibility; exposed an unambiguous screened-index field; and
  reported raw and buffered active KKT constraints separately.
- `Project4/results/optimization/campaign.json` and `campaign.md`: regenerated
  the evidence presentation without changing the existing authoritative
  numerical results. The current linear reference is feasible, all 20 fins
  remain active, and the topology bonus is not claimed.
- `Project4/tests/test_optimize.py`: strengthened the Agent 3 evidence contract
  and added a regression comparing campaign masses, geometry, load responses,
  topology outcome, and KKT evidence with canonical `site/assets/results.json`.
- This handoff: marked the original PR #16 numbers as historical and recorded
  the current-main audit.

### Commands and observed results

- Human gate validation through `python -m Project4.heatsink.run_all
  --config Project4/config.yaml --check-gates`: passed.
- Campaign reproduction to an isolated `/tmp` output: completed with status
  `complete_with_authoritative_model_blockers`; the same feasibility,
  20-fin, no-topology-bonus, and KKT conclusions were reproduced. Minor
  optimizer/timing variation was not substituted for the canonical integrated
  results.
- Focused Agent 3 suite:
  `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest
  Project4/tests/test_optimize.py Project4/tests/test_topology.py -q -p
  no:cacheprovider`: **10 passed in 6.90 s** on the finalized branch.
- Full suite in an isolated copy, using the repository virtual environment:
  `python -m pytest Project4/tests -q -p no:cacheprovider`: **42 passed in
  25.66 s** on the finalized branch.
- Static-site build in the isolated copy: passed.
- `node --check Project4/site/assets/viewer.js`: passed.
- `git diff --check`: passed.

### Assumptions and limitations

- Merged `main` and its approved DEC-002/DEC-003 configuration are
  authoritative. The earlier 50 mm / `h=10` Agent 3 numbers remain preserved
  below only as historical PR evidence.
- The optimization evidence demonstrates a converged feasible local solution,
  not global optimality. All tested starts converge to the all-solid topology.
- A filtered low-raw-density screen cannot establish a physically removed fin;
  no topology bonus is claimed.

### Issues and remaining out-of-scope findings

- Agent 3 issue #10 was updated with the current-model supersession and audit
  evidence: https://github.com/lucasszokol/DesOptCCLP/issues/10#issuecomment-7170956046
- Existing Agent 4 issue #11 was updated instead of creating a duplicate:
  https://github.com/lucasszokol/DesOptCCLP/issues/11#issuecomment-7170954497
  It records the untouched serializer/viewer mismatch between raw and buffered
  topology-start constraints, ambiguous KKT stationarity labeling, a hard-coded
  20-fin report claim, and missing final-topology schema coverage.
- No site, serializer, schema, configuration, solver verification, benchmark
  truth, approval, workflow, or other-agent-owned file was changed.

### Final commit information

- Current-main merge commit: `7218e1b35ff6cf92a4ee1d8fbbe9bcf5d1a8a48a`.
- Audit implementation commit: `0a10e3bb6fd0efb0e1a9f06795803a58ffa1e601`.
- The final handoff update is the subsequent commit containing this section.

- Agent/account: Polina / `pkondratkippy`
- GitHub issue: https://github.com/lucasszokol/DesOptCCLP/issues/10
- Branch: `agent/optimization-topology`
- Implementation commit SHA: `863f58358f6f65cc070b4079a1b20ed70e900f3d`
- Pull request: https://github.com/lucasszokol/DesOptCCLP/pull/16
- Started/finished (America/Phoenix): 2026-11-17 / 2026-11-17 15:18 MST

## Scope completed

- Added three documented nonlinear fixed-topology starts and three documented
  topology starts, with deterministic accepted-run selection.
- Preserved the linear fixed-topology optimizer failure as an infeasible
  reference instead of relabeling it as a successful optimum.
- Executed SIMP continuation at the configured penalties, raw-density
  thresholding, filtered-density validation, and height re-optimization.
- Scaled the `trust-constr` variables to a unit box while mapping every
  evaluation back to positive physical heights. This fixes the non-positive
  element-length crash without weakening the element guard.
- Added a strictly interior feasible KKT seed search, exact zero objective
  Hessian, physical stationarity/complementarity calculations, accepted-run
  feasibility checks, histories, and per-stage timing.
- Added generated JSON and Markdown evidence, including fixed/topology mass
  comparisons, active-constraint multipliers, raw/filtered discreteness, and
  a maximum-height one-fin-removal screen.

## Files changed

- `Project4/heatsink/optimize.py`
- `Project4/heatsink/campaign.py`
- `Project4/heatsink/topology.py`
- `Project4/tests/test_optimize.py`
- `Project4/tests/test_topology.py`
- `Project4/results/optimization/campaign.json`
- `Project4/results/optimization/campaign.md`
- `Project4/coordination/handoffs/agent-3.md`

No accidental Agent 4 stash content was inspected, applied, copied, or reused.

## Commands and observed results

- `git pull --ff-only origin main`: already up to date before branch creation.
- Human-gate YAML validation: approval exists and is exactly `true`; benchmark
  status is `student_verified`; student attestation is nonempty; both files are
  tracked on `main`.
- Baseline focused tests: 3 passed.
- Baseline campaign: reproduced the non-positive-height `trust-constr` crash.
- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m
  Project4.heatsink.campaign --config Project4/config.yaml --output
  Project4/results/optimization`: completed in 24.970 s and generated status
  `complete_with_authoritative_model_blockers`.
- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest
  Project4/tests/test_optimize.py Project4/tests/test_topology.py -q`: 8 passed
  in 4.44 s after final changes.
- Full suite in an isolated copy (to avoid writing Agent 4's `_site` path):
  `python -m pytest Project4/tests -q -p no:cacheprovider`: 24 passed in
  11.34 s.
- `git diff --check`: passed with no output before the implementation commit.
- Final pre-push verification after refreshing `origin/main`: focused suite
  8 passed in 4.38 s; full isolated suite 24 passed in 10.99 s; the static
  site built successfully in the isolated copy; `node --check` passed; and
  `git diff --check` passed. The branch was 0 commits behind and 2 ahead of
  `origin/main` before this handoff-only update.

## Evidence produced

- All three nonlinear fixed-topology starts converged to the same feasible
  design within numerical precision.
- All three topology starts and SIMP penalties 1, 2, and 3 converged to the
  same feasible all-solid design.
- Nonlinear fixed/topology/threshold mass: approximately 0.1733531364 kg.
- KKT-polished mass: 0.1733531519 kg; maximum scaled constraint
  `-6.50673e-10`; `trust-constr` ended successfully by `gtol`.
- KKT physical stationarity infinity norm: `1.60943e-9`.
- Constraint complementarity infinity norm: `1.02400e-8`.
- Bound complementarity infinity norm: `1.07639e-8`.
- Constraint violation: `0`.
- The overload constraint is active. Its normalized-objective multiplier is
  `14.7255`, equivalent to about `1.79578 kg` per unit relaxation of the
  scaled constraint.
- Raw and post-threshold filtered density vectors contain no intermediate
  values in `(0.01, 0.99)`; grayness is zero.
- Threshold height re-optimization remains feasible.

## Material discoveries and decisions

- The configured linear fixed-topology problem is infeasible: even the
  maximum-material design has maximum scaled constraint `0.0310537`. Its
  SLSQP exit remains visibly unsuccessful.
- The feasible topology optimum retains all 20 fins. Removing each candidate
  fin individually at maximum height was screened with the final nonlinear
  penalty; every case is infeasible. The best one-fin deletion still has
  maximum scaled constraint `0.00434207`, above the `1e-4` tolerance.
- Therefore no topology bonus is claimed. The campaign establishes a valid
  negative engineering result under the frozen specification rather than
  forcing a visually sparse but infeasible topology.
- SciPy's bound-multiplier sign convention is positive for an active upper
  bound; the physical complementarity calculation and regression test encode
  that convention.

## Known limitations or unresolved risks

- Completing the requested feasible linear comparison and a topology with at
  least one vanished fin requires a human-approved specification/configuration
  change. Issue #10 records the proposed decision; Agent 3 did not implement
  unapproved values.
- Campaign runtimes and optimizer histories are deterministic in structure but
  wall-clock timing naturally varies by machine.
- The evidence has no claim of global optimality. The three fixed starts and
  three topology starts converged to the same local result.

## Out-of-lane defects reported but not edited

- The frozen linear physics/height bounds do not contain a feasible design.
  `Project4/config.yaml` and `Project4/SPECIFICATION.md` are read-only for
  Agent 3; the finding is documented in Issue #10 and generated evidence.
- The current integration serializer treats every unsuccessful comparison
  stage as making the whole canonical payload incomplete. Because the linear
  reference is provably infeasible, Agent 5 must decide how to represent this
  honest comparison after any approved shared-contract decision. Agent 3 did
  not edit `run_all.py`, `serialize.py`, configuration, or site files.

## Integration notes

- Regenerate Agent 3 evidence with:
  `python -m Project4.heatsink.campaign --config Project4/config.yaml --output Project4/results/optimization`.
- The full integration path may call `run_campaign(model)` as before; existing
  fields (`linear_fixed`, `nonlinear_fixed`, `continuation`,
  `threshold_polish`, `kkt_polish`, and `binary_density`) remain available.
- New fields expose all starting-point runs, the KKT seed label, and total
  campaign time for audit.
- Do not merge the accidental Agent 4 stash into this branch.

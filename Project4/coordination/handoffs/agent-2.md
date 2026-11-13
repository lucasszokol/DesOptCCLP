# Handoff: P4-A2 — adjoint and Taylor evidence

- Agent: Codex, Agent 2 lane for Christian Miranda.
- Issue: https://github.com/lucasszokol/DesOptCCLP/issues/9
- Branch: `agent/adjoint-sensitivity`
- Base: `e4d8861cb8ff259ee2a93455fdf05c8505e31ba6`
- Verification implementation commit: `12fc83a1ae0dfbd04e1a78458dd4ca10ca1298aa`.
  Generated evidence records this commit and exact source SHA-256 hashes; the
  following evidence/handoff commit contains no verification implementation changes.
- PR: linked from issue #9 after branch publication; no merge authorized.
- Work date (America/Phoenix): 2026-11-12.

## Scope completed

Expanded verification for both constraints and both variable families, both linear
and nonlinear states, and all configured SIMP penalties. Added seeded random
directions, all-state KS derivative tests, family-specific all-variable FD errors,
a standalone gated reproduction command, and a generated Taylor plot.

Corrected the FD timing baseline: perturbed designs now call state-only solves,
not `response_with_adjoint`. A regression counts adjoint invocations. The KS tests
also include a deliberately corrupted gradient to confirm that failures are detected.
No tolerance was relaxed. Mass is state independent and uses its direct gradient.

## Files changed

- `Project4/heatsink/verification.py`
- `Project4/tests/test_sensitivity.py`
- `Project4/results/sensitivity/README.md`
- `Project4/results/sensitivity/sensitivity.json`
- `Project4/results/sensitivity/sensitivity.md`
- `Project4/results/sensitivity/taylor_checks.png`
- This handoff.

## Commands and observed results

Commands were run from the repository root in a local Windows Python 3.13 virtual
environment created with `python -m venv --system-site-packages .venv` and the
declared requirements installed. Exact Python/NumPy/SciPy versions are in JSON.

```powershell
.\.venv\Scripts\python.exe -m Project4.heatsink.run_all --check-gates
# Human gates passed.

.\.venv\Scripts\python.exe -m pytest Project4/tests -q
# Untouched main baseline: 19 passed in 16.19s.
# Expanded implementation: 22 passed in 29.91s.

.\.venv\Scripts\python.exe -m pytest Project4/tests/test_sensitivity.py -q
# Expanded implementation: 6 passed in 28.45s.

.\.venv\Scripts\python.exe -m Project4.heatsink.verification --config Project4/config.yaml
# Sensitivity evidence: passed (72 sweeps).

.\.venv\Scripts\python.exe -m Project4.heatsink.site --source Project4/site
# Built static report successfully (ignored generated _site directory).

node --check Project4/site/assets/viewer.js
# Exit 0.

git diff --check
# Exit 0, no whitespace errors.

git fetch origin main
git rebase origin/main
# Current branch agent/adjoint-sensitivity is up to date.
```

The focused and full suites were rerun after the required main refresh/rebase.
Post-rebase results: focused **6 passed in 28.59s**, full **22 passed in 30.72s**.
The final evidence command was rerun from the implementation commit so its
provenance identifies committed code, rather than an uncommitted working copy.
The prior timing measurement is superseded, not an independent reference truth.

## Evidence and interpretation

See `results/sensitivity/README.md` for the adjoint/KS/mass derivatives, reproduction
instructions, coverage, and limitations. JSON retains every direction, design,
step, derivative error, remainder, fit window, source hash, and timing observation.
The original acceptance criteria are unchanged: relative directional errors at most
1e-5, with Taylor slopes from 1.8 to 2.2 before the small-step error floor.

Final generated results: 72/72 sweeps passed; slopes 1.980661--2.085947;
worst best directional relative error 4.821864e-8; maximum full-gradient relative
error 1.135267e-7; maximum KS relative error 8.247071e-9; maximum mass-direction
relative error 6.616019e-10. Measured speedups range from 34.3x to 69.5x; see the
per-case table for machine-dependent timings. Source hashes were checked against
the local files after generation, and the generated plot was visually inspected.

The course brief was retrieved and reviewed:
https://designinformaticslab.github.io/DesignOptimization2025/project4.html
Its sensitivity rubric requires every constraint and variable type plus a cost
comparison. The lane prompt additionally requests relevant linear/nonlinear states;
this delivery covers both, rather than assuming only the final N2 model matters.

## Human-gate compliance

`approvals.yaml` records approval and `benchmark_truth.yaml` is student-verified
with a nonempty attestation. The actual gate command passed before validation.
Neither file nor the students' worksheet was edited or regenerated. No benchmark
answers were derived or replaced. Solver, model, configuration, optimization, and
site source files remain unchanged. No credentials are included.

## Out-of-lane findings and integration

1. Reported to Agent 3 on issue #10:
   https://github.com/lucasszokol/DesOptCCLP/issues/10#issuecomment-6840021877
   Raw binary thresholding is followed by filtering in `split_design`. An interior
   raw density of 0.001 between two retained fins gives effective density 0.4006.
   This does not affect an all-solid design, but mixed patterns require explicit
   retained-fin validation. No shared-model or topology changes were made.
2. Existing Agent 3/5 issue comments already document optimization/KKT problems and
   a proposed specification change. These are not repaired or approved by Agent 2.
   Validation here uses merged main's configuration only, not an unmerged proposal.
3. Existing `run_all.py` remains API-compatible, but still calls its nonlinear-only
   V7 subset and can overwrite the expanded JSON/Markdown. Agent 5 should wire the
   full standalone suite into the integrated reproduction pipeline if the final
   report will use all coverage. The standalone command regenerates all evidence
   without launching the optimization campaign.

## Limitations

This is local derivative consistency evidence at an interior nonuniform design,
not physical validation, optimization feasibility, or a test of nonsmooth binary
thresholding. All-variable tests use p=3; directional sweeps cover p=1,2,3. Timings
are single warmed measurements and are sensitive to machine load. The fixed first
four-step slope window is documented in advance; all smaller steps remain in the
evidence so roundoff and solver-error effects are visible. No claim of successful
full optimization, deployed website, or final course score is made.

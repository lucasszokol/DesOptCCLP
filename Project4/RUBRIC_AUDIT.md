# Project 4 Rubric Audit

This file is a live evidence ledger. “Blocked” means the implementation exists
but the course-required student input or external publication action has not
yet occurred; it does not mean the criterion is being claimed as complete.

| Criterion | Points | Current evidence | Status |
|---|---:|---|---|
| Structure and formulation | 10 | `SPECIFICATION.md`, `config.yaml`, explicit formulas, property sources, and `approvals.yaml` | Loads and limits approved; DEC-003 numerical settings approved 2026-11-19 |
| Analysis and verification | 20 | `results/verification/verification.md`: 20/20 V1--V6 checks pass; the results JSON also records the production nonlinear fin comparison against an independent numerical BVP, tangent check, and mesh refinement | Passed; reference is numerical rather than student-derived exact truth |
| Sensitivity analysis | 20 | `results/sensitivity/sensitivity.md` records both constraints, variable families, physics modes, and configured SIMP penalties | Expanded Agent 2 checks integrated in the reproducibility command; the output records each pass/fail result |
| Optimization | 15 | SLSQP stages, three topology starts, continuation, threshold re-optimization, unit-box trust-constr KKT polish; `site/assets/results.json` | Revised campaign passes with the approved numerical reserve and design-level mesh checks |
| Nonlinear component | 15 | Natural-convection/radiation N2 residual, Newton solve, consistent tangent, passing V6 benchmark, linear/N2 results | Local comparison generated; linear reference coefficient is a separate modeling choice |
| Website and 3D | 10 | Report, Three.js geometry, per-fragment bilinear base field, history, hover and touch inspection, metrics, JSON contract | Browser checks and current deployment evidence recorded in the handoff |
| Reproducibility | 5 | Repository-root command, schema test, Pages workflow, enforced human/V1--V7 and optimization gates | Clean Python 3.10 environment reproduced both masses and passed 21 tests; Python 3.11 CI ran the complete campaign and schema validation successfully at 187fe1c |
| Presentation | 5 | Report sections and generated numerical tables | Team reported its review on 2026-11-16; deployed artifact and submission remain to be checked |
| Bonus: fully nonlinear | +5 | N2 Newton, analytic tangent, implicit adjoint, nonlinear benchmark and comparison | Local evidence produced; final report review pending |
| Bonus: topology | +5 | Ground-structure densities, filter, SIMP continuation, threshold and fixed-topology comparison | Current optimum is all-solid; mixed topology and threshold-filter behavior remain unverified, so bonus is not claimed |
| Bonus: uncertainty | +5 | Four paired power/ambient scenarios, constrained optimization and 8 directional gradient checks | Local evidence produced; assumptions illustrative rather than calibrated probabilities |

## Mandatory completion evidence still missing

1. Implement discrete topology reanalysis if claiming a vanished-fin bonus.
2. Verify the latest public deployment in a private window after changes.
3. Confirm the participation-sheet URL and submit repository and site URLs on Canvas.

The DEC-002 human decision is recorded in
`coordination/decisions/DEC-002-optimization-feasibility.md`: the approved
domain uses a 55 mm height cap, the linear comparison uses
15 W/(m² K), and uncertainty is the backup bonus path.

## Bugs caught so far

- Feasibility bounding rejected the original 100/125 W requirements because
  the maximum-material design could not pass them; corrected study loads are
  50/60 W.
- A repository-root CI rehearsal found that tests imported the package only
  when run from inside `Project4`; a shared test bootstrap now makes the local
  and GitHub Actions commands identical.
- The first full gated campaign reached `trust-constr` and exposed an
  out-of-bounds trial height that correctly triggered the positive element-
  length guard. The reproduction and ownership-safe fix request are recorded
  in GitHub issue #10.
- The original sensitivity cost comparison accidentally computed adjoints for
  each finite-difference perturbation; it now times state-only solves.

No score is claimed until the corresponding final evidence exists.

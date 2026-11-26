# Project 4 Rubric Audit

This file is a live evidence ledger. “Blocked” means the implementation exists
but the course-required student input or external publication action has not
yet occurred; it does not mean the criterion is being claimed as complete.

Corrective audit baseline: `f4d3e5b26870136f66f6ee034008e016aecab93d`.
The final corrective state was validated locally on 2026-11-25; its commit is
recorded by Git history.

| Criterion | Points | Current evidence | Status |
|---|---:|---|---|
| Structure and formulation | 10 | `SPECIFICATION.md`, `config.yaml`, explicit formulas, property sources, and `approvals.yaml` | Loads and limits approved; DEC-003 numerical settings approved 2026-11-19 |
| Analysis and verification | 20 | `results/verification/verification.md`: 20/20 V1--V6 checks pass; the results JSON also records the production nonlinear fin comparison against an independent numerical BVP, tangent check, and mesh refinement | Passed; reference is numerical rather than student-derived exact truth |
| Sensitivity analysis | 20 | `results/sensitivity/sensitivity.md` records both constraints, variable families, physics modes, and configured SIMP penalties | Expanded Agent 2 checks integrated in the reproducibility command; the output records each pass/fail result |
| Optimization | 15 | SLSQP stages, three topology starts, continuation, threshold re-optimization, unit-box trust-constr KKT polish; `site/assets/results.json` | Revised campaign passes with the approved numerical reserve and design-level mesh checks; the report distinguishes physical stationarity from scaled optimizer optimality |
| Nonlinear component | 15 | Natural-convection/radiation N2 residual, Newton solve, consistent tangent, passing V6 benchmark, linear/N2 results | Local comparison generated; linear reference coefficient is a separate modeling choice |
| Website and 3D | 10 | Report, Three.js geometry, per-fragment bilinear base field, history, hover and touch inspection, metrics, JSON contract | The corrected local page passed desktop and 390 px checks with WebGL, MathJax, animation, click inspection, and no page-wide overflow; the deployed page still needs the final human private-window inspection |
| Reproducibility | 5 | Repository-root command, schema test, Pages workflow, enforced human/V1--V7 and optimization gates | The full command passed from an isolated copy of the corrective working tree on macOS/Python 3.11.18; all 44 local tests passed. Linux verification of the corrective commit remains pending the post-commit CI run |
| Presentation | 5 | Report sections and generated numerical tables | Report content and static presentation are complete; final deployed desktop/phone review and submission remain human actions |
| Bonus: fully nonlinear | +5 | N2 Newton, analytic tangent, implicit adjoint, nonlinear benchmark and comparison | Evidence and final report comparison are present; instructor credit remains external |
| Bonus: topology | +5 | Ground-structure densities, filter, SIMP continuation, threshold and fixed-topology comparison | The accepted result retains all 20 candidate fins and no discrete removed-fin feasibility result exists; the bonus is explicitly not claimed |
| Bonus: uncertainty | +5 | Four paired power/ambient scenarios, constrained optimization and 8 directional gradient checks, each retaining a seven-step central-difference sweep | Local evidence passes without relaxing the `1e-5` tolerance; scenarios are illustrative rather than calibrated probabilities |

## Remaining human-only completion actions

1. After deployment, inspect the corrected live site in a private window at
   desktop and approximately 390 px width, including formulas and interactions.
2. Confirm the participation-sheet URL.
3. Submit the repository and site URLs on Canvas.

A discrete removed-fin reanalysis would be required before claiming the
topology bonus, but that bonus is not claimed and is not a submission blocker.

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

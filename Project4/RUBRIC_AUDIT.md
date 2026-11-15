# Project 4 Rubric Audit

This file is a live evidence ledger. “Blocked” means the implementation exists
but the course-required student input or external publication action has not
yet occurred; it does not mean the criterion is being claimed as complete.

| Criterion | Points | Current evidence | Status |
|---|---:|---|---|
| Structure and formulation | 10 | `SPECIFICATION.md`, `config.yaml`, explicit formulas, property sources, and `approvals.yaml` | Team approved 2026-11-11 |
| Analysis and verification | 20 | `results/verification/verification.md`: 20/20 V1--V6 checks pass, including Q4 convergence, balance, invariance, units, and Newton tangent | Passed |
| Sensitivity analysis | 20 | `results/sensitivity/sensitivity.md`: both constraints and variable families pass; Taylor slopes 1.98--2.07 and all-variable relative error 2.28e-8 | Passed |
| Optimization | 15 | Scaled SLSQP stages, continuation, two asymmetric starts, threshold re-optimization, trust-constr KKT polish; `site/assets/results.json` | Local full campaign passes, including feasibility and KKT; all three topology starts return the all-solid design |
| Nonlinear component | 15 | Natural-convection/radiation N2 residual, Newton solve, consistent tangent, passing V6 benchmark, linear/N2 results | Local comparison generated; linear reference coefficient is a separate modeling choice |
| Website and 3D | 10 | Local report, Three.js geometry, nodal field, history, hover and touch inspection, metrics, JSON contract | Local desktop and 390 px checks exercised hover, tap, animation and layout; live deployment and private-window check pending |
| Reproducibility | 5 | Repository-root command, schema test, Pages workflow, enforced human/V1--V7 and optimization gates | Clean Python 3.10 environment reproduced both masses and passed 21 tests; Python 3.11 CI ran the complete campaign and schema validation successfully at 96c470e |
| Presentation | 5 | Report sections and generated numerical tables | Team review and final editing pending |
| Bonus: fully nonlinear | +5 | N2 Newton, analytic tangent, implicit adjoint, nonlinear benchmark and comparison | Local evidence produced; final report review pending |
| Bonus: topology | +5 | Ground-structure densities, filter, SIMP continuation, threshold and fixed-topology comparison | Current optimum is all-solid; mixed topology and threshold-filter behavior remain unverified, so bonus is not claimed |
| Bonus: uncertainty | +5 | Four paired power/ambient scenarios, constrained optimization and 8 directional gradient checks | Local evidence produced; assumptions illustrative rather than calibrated probabilities |

## Mandatory completion evidence still missing

1. Review independent branches and integrate their evidence; implement discrete topology reanalysis if claiming a vanished-fin bonus, and review robust-study reporting.
2. Rerun CI after future changes and verify the final deployed artifact.
3. Obtain team review of the AI-use statement; merge and deploy with action-time approval; verify the public site in a private window.
4. Confirm the overdue participation-sheet URL and submit repository and site URLs on Canvas by a student.

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

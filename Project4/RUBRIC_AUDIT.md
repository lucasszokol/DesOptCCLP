# Project 4 Rubric Audit

This file is a live evidence ledger. “Blocked” means the implementation exists
but the course-required student input or external publication action has not
yet occurred; it does not mean the criterion is being claimed as complete.

| Criterion | Points | Current evidence | Status |
|---|---:|---|---|
| Structure and formulation | 10 | `SPECIFICATION.md`, `config.yaml`, explicit formulas, property sources, and `approvals.yaml` | Team approved 2026-11-11 |
| Analysis and verification | 20 | `results/verification/verification.md`: 20/20 V1--V6 checks pass, including Q4 convergence, balance, invariance, units, and Newton tangent | Passed |
| Sensitivity analysis | 20 | `results/sensitivity/sensitivity.md`: both constraints and variable families pass; Taylor slopes 1.98--2.07 and all-variable relative error 2.28e-8 | Passed |
| Optimization | 15 | Scaled SLSQP stages, continuation, threshold re-optimization, trust-constr KKT polish | Campaign reaches final KKT stage; blocked by tracked bound-handling defect in issue #10 |
| Nonlinear component | 15 | Natural-convection/radiation N2 residual, Newton solve, consistent tangent, and passing V6 scalar benchmark | Verification passed; final design comparison pending |
| Website and 3D | 10 | Live GitHub Pages report, responsive Three.js geometry, temperature scale, hover, metrics, JSON contract | Pages deploys successfully; final optimization history and phone-width QA pending |
| Reproducibility | 5 | Pinned requirements, repository-root command, schema test, Pages workflow, and enforced human/V1--V7 gates | Human and verification gates pass; full command currently fails at tracked KKT bound defect |
| Presentation | 5 | Required report sections and concise engineering narrative | Final numeric tables/figures pending |
| Bonus: fully nonlinear | +5 | N2 Newton, analytic tangent, implicit adjoint, and passing nonlinear benchmark evidence | Verification passed; final comparison pending |
| Bonus: topology | +5 | Ground-structure densities, filter, SIMP continuation, threshold and fixed-topology comparison | Final optimized result pending |

## Mandatory completion evidence still missing

1. Successful full `run_all` optimization execution and final schema validation.
2. Rendered-site desktop and 390 px visual QA.
3. Repository and site URL submission on Canvas by a student.

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

No score is claimed until the corresponding final evidence exists.

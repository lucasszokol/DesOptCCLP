# Project 4 Rubric Audit

This file is a live evidence ledger. “Blocked” means the implementation exists
but the course-required student input or external publication action has not
yet occurred; it does not mean the criterion is being claimed as complete.

| Criterion | Points | Current evidence | Status |
|---|---:|---|---|
| Structure and formulation | 10 | `SPECIFICATION.md`, `config.yaml`, explicit formulas and primary property sources | Awaiting team approval |
| Analysis and verification | 20 | Custom Q4/line FE kernels, nonlinear residual/tangent, conservation and invariance tests | Blocked on student benchmark truth |
| Sensitivity analysis | 20 | Analytic residual design Jacobian, discrete adjoint, directional test to 1e-5, Taylor/cost pipeline | Implemented; final plots pending gated run |
| Optimization | 15 | Scaled SLSQP stages, continuation, threshold re-optimization, trust-constr KKT polish | Implemented; execution blocked on approval |
| Nonlinear component | 15 | Natural-convection/radiation N2 residual, Newton solve, consistent tangent, linear/N2 comparison pipeline | Benchmark truth and final comparison pending |
| Website and 3D | 10 | Jekyll report, responsive Three.js geometry, temperature scale, hover, metrics, JSON contract | Local source implemented; final history and live URL pending |
| Reproducibility | 5 | Pinned requirements, repository-root command, schema test, Pages workflow | Command intentionally stops at human gate |
| Presentation | 5 | Required report sections and concise engineering narrative | Final numeric tables/figures pending |
| Bonus: fully nonlinear | +5 | N2 Newton + implicit adjoint code and nonlinear benchmark worksheet | Final benchmark evidence pending |
| Bonus: topology | +5 | Ground-structure densities, filter, SIMP continuation, threshold and fixed-topology comparison | Final optimized result pending |

## Mandatory completion evidence still missing

1. Student-authored `tests/benchmark_truth.yaml` with attestation.
2. Team-authored `approvals.yaml` accepting the corrected 50/60 W specification.
3. Successful gated `run_all` execution and final schema validation.
4. Rendered-site desktop and 390 px visual QA.
5. GitHub Pages enablement and private-window verification.
6. Repository and site URL submission on Canvas by a student.

## Bugs caught so far

- Feasibility bounding rejected the original 100/125 W requirements because
  the maximum-material design could not pass them; corrected study loads are
  50/60 W.
- A repository-root CI rehearsal found that tests imported the package only
  when run from inside `Project4`; a shared test bootstrap now makes the local
  and GitHub Actions commands identical.

No score is claimed until the corresponding final evidence exists.

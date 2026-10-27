# Project 3 Teammate 2 handoff

**Branch:** `project3/teammate2-pinn-audit`
**Base commit:** `713111f` (`origin/main` at the start of the audit)
**Scope:** Teammate 2 only. No Project 1, Project 2, solver, training, test, or production-output files were changed.

## Completed

- Audited PINN residuals, scaling, sampling, controlled conditions, losses, gradient diagnostics, adaptive weights, deterministic execution, failure handling, runtime reporting, and checkpoint behavior.
- Inspected all course lecture-note decks relevant to gradients, curvature, Adam, L-BFGS, stochastic optimization, and project handoff.
- Inspected the committed production reference and quick smoke-test artifacts.
- Created [`reviews/pinn_experiment_audit.md`](reviews/pinn_experiment_audit.md), including the 27-run controlled matrix, cause-discrimination criteria, proposed tests, progress/checkpoint design, one-week ablation plan, and a threshold-free rule for the vanilla comparative-worsening claim.
- Preserved the assignment's fixed 25% Reynolds number 40 median-error improvement threshold.
- Did not launch another production sweep or modify an active run's files.

## Key findings

- Core residual equations and vanilla-versus-balanced controls are implemented correctly.
- The checkout contains no completed production PINN run, so no scientific convergence conclusion is available.
- Training has no durable intermediate history or resumable Adam checkpoint.
- L-BFGS has no component or gradient diagnostics.
- Zero-norm component gradients can cause named cosine fields to disappear.
- Non-finite gradient norms are not rejected before adaptive-weight projection.
- Wake sampling is deliberate, but near-cylinder fluid sampling and independent residual validation are missing.
- Existing `model.pt` detection is not a safe completeness or resume check.

## Verification status

- Documentation coverage: complete against every required Teammate 2 deliverable.
- Automated tests: the bundled Python 3.12 runtime completed all ten discovered tests. Eight passed and the two PyTorch-dependent tests were skipped because PyTorch is not installed on the Apple M1 review machine. The repository's committed status states that all ten tests pass on the production CUDA environment.
- Test command: `/Users/charliegreen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest tests.test_project3_pinn -v` from `Project 3/`.
- Production training: intentionally not run.

## Remaining team actions

1. Review and approve the proposed logging/checkpoint design before implementation.
2. Finish or safely stop the already active run before changing training code or its output directory.
3. Implement the proposed tests and checkpoint support in a separate change.
4. Generate adequate Reynolds number 20 and 40 references, then complete the fixed 27-run matrix.
5. Apply the predeclared decision rules without selecting a new accuracy or stationarity threshold after seeing results.

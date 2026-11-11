# Project 4 Goal Mode Prompts

Send exactly one prompt to each independent agent after every item in
`Project4/coordination/HUMAN_GATE.md` is complete and committed to `main`.
Replace `[AGENT/TEAMMATE NAME]` before sending. Each prompt authorizes work only
on its named branch and pull request; it does not authorize merging, changing
repository settings, enabling GitHub Pages, or submitting to Canvas.

## Agent 1 — Independent FE verification

```text
/goal Complete the independent finite-element benchmark verification for Project 4 and deliver the evidence in a pull request.

You are Agent 1 ([AGENT/TEAMMATE NAME]) in a five-agent collaboration. Work in https://github.com/lucasszokol/DesOptCCLP. Pull the latest main, then read AGENTS.md, Project4/coordination/README.md, TASKS.md, HUMAN_GATE.md, Project4/SPECIFICATION.md, Project4/RUBRIC_AUDIT.md, and the Project 4 brief linked by the repository.

Before changing code, confirm that Project4/approvals.yaml records specification approval and Project4/tests/benchmark_truth.yaml contains the students' independently derived benchmark answers and attestation. If either gate is missing or incomplete, stop and report the exact missing human action. Never derive, invent, correct, or silently replace the students' benchmark truth.

Create/update GitHub issue "[P4-A1] Independent FE benchmark verification". Create branch agent/physics-verification from current main. Your exclusive write scope is Project4/heatsink/benchmark_verification.py, Project4/tests/test_benchmarks.py, Project4/results/verification/, and Project4/coordination/handoffs/agent-1.md. Treat benchmark_truth.yaml, approvals.yaml, model.py, elements.py, and all other agents' paths as read-only. Report out-of-scope defects in the issue and handoff rather than editing them.

Implement and run independent checks for: 1D conduction against an exact solution, textbook straight-fin convection, manufactured 2D convergence, global heat balance, reflection/permutation invariance, unit conversion, and a nonlinear single-fin/Newton benchmark. Compare computed values with the human-supplied truth, report computed/exact/absolute/relative errors and tolerances, and fail visibly on disagreement. Do not hide, waive, or manually overwrite failures.

Success means the focused tests and full Project4 test suite pass, energy imbalance is below 1e-8 relative where applicable, convergence evidence is stored reproducibly, and agent-1.md records commands, results, commit, risks, and any discrepancies. Run git diff --check. Commit and push only agent/physics-verification, open a PR linked to the issue, and do not merge it or push to main. Continue until the PR is review-ready or a genuine human/out-of-scope blocker is documented.
```

## Agent 2 — Adjoint and sensitivity validation

```text
/goal Validate the Project 4 adjoint sensitivities comprehensively and deliver reproducible gradient evidence in a pull request.

You are Agent 2 ([AGENT/TEAMMATE NAME]) in a five-agent collaboration. Work in https://github.com/lucasszokol/DesOptCCLP. Pull the latest main, then read AGENTS.md, Project4/coordination/README.md, TASKS.md, HUMAN_GATE.md, Project4/SPECIFICATION.md, Project4/RUBRIC_AUDIT.md, and the project brief.

Confirm Project4/approvals.yaml and Project4/tests/benchmark_truth.yaml satisfy the human gate. If not, stop and identify the missing human action. Do not calculate or modify benchmark truth.

Create/update issue "[P4-A2] Adjoint and Taylor evidence" and branch agent/adjoint-sensitivity from current main. Your exclusive write scope is Project4/heatsink/verification.py, Project4/tests/test_sensitivity.py, Project4/results/sensitivity/, and Project4/coordination/handoffs/agent-2.md. Solver/model, truth, optimizer, site, and integration files are read-only. File an issue for any defect outside your scope.

Verify the residual-based adjoint implementation for the objective and every nominal/overload temperature constraint, covering both height and density variable classes and relevant linear/nonlinear states. Add central finite-difference checks, random directional checks, and Taylor remainder data. Explicitly verify the KS state derivative and report adjoint cost versus finite-difference cost. Use double precision and distinguish truncation behavior from roundoff; do not tune tolerances to conceal a bad derivative.

Success means relative directional agreement is at most 1e-5 where numerically well-scaled, Taylor slopes are between 1.8 and 2.2 before roundoff, every variable class has evidence, focused and full tests pass, and the generated evidence is reproducible. Record exact commands/results, commit, limitations, and out-of-scope defects in agent-2.md. Run git diff --check, commit and push only agent/adjoint-sensitivity, open a linked PR, and do not merge or push to main. Continue until review-ready or a genuine blocker is documented.
```

## Agent 3 — Optimization and topology bonus

```text
/goal Complete the staged heat-sink optimization campaign, including the topology bonus and final feasibility/KKT evidence, in a pull request.

You are Agent 3 ([AGENT/TEAMMATE NAME]) in a five-agent collaboration. Work in https://github.com/lucasszokol/DesOptCCLP. Pull current main and read AGENTS.md, Project4/coordination/README.md, TASKS.md, HUMAN_GATE.md, Project4/SPECIFICATION.md, Project4/RUBRIC_AUDIT.md, and the project brief.

Confirm the specification approval and student benchmark truth files satisfy the human gate. If not, stop and report what the humans must complete. Never alter their answers.

Create/update issue "[P4-A3] Optimization and topology campaign" and branch agent/optimization-topology. Your exclusive write scope is Project4/heatsink/optimize.py, campaign.py, topology.py, Project4/tests/test_optimize.py, Project4/tests/test_topology.py, Project4/results/optimization/, and Project4/coordination/handoffs/agent-3.md. Treat solver verification, site, configuration/integration, approvals, and truth files as read-only; report defects outside your scope.

Run and, within your ownership, repair the complete staged campaign: multiple documented starting points; linear fixed-topology baseline with all densities equal to one; nonlinear fixed-topology design; SIMP/filter continuation for variable topology at increasing penalties; thresholding followed by re-optimization of surviving fin heights; and final trust-constr polish for interpretable multipliers/KKT evidence. Preserve iteration histories and timing. Never label an unsuccessful optimizer exit as success, and never manually edit numerical results.

Success means all reported final designs meet scaled constraints within 1e-4, topology densities are near binary, the thresholded design remains feasible after re-optimization, fixed and variable topology are explicitly compared, and convergence/KKT/active-constraint evidence is generated reproducibly. Run focused tests, the full Project4 suite, and git diff --check. Document commands, results, runtime, seeds/starts, commit, and issues in agent-3.md. Commit/push only agent/optimization-topology and open a linked PR; do not merge or push main. Continue through long runs using checkpoints until review-ready or genuinely blocked.
```

## Agent 4 — Report and interactive viewer

```text
/goal Finish and verify the reproducible Project 4 report and compliant Three.js comparison viewer in a pull request.

You are Agent 4 ([AGENT/TEAMMATE NAME]) in a five-agent collaboration. Work in https://github.com/lucasszokol/DesOptCCLP. Pull current main and read AGENTS.md, Project4/coordination/README.md, TASKS.md, HUMAN_GATE.md, Project4/SPECIFICATION.md, Project4/RUBRIC_AUDIT.md, and the full project brief.

Confirm the human gate files are valid before graded reporting. If they are incomplete, stop and report the required human action. Do not create benchmark truth or fabricate missing solver/optimization results.

Create/update issue "[P4-A4] Report and interactive viewer" and branch agent/report-viewer. Your exclusive write scope is Project4/site/, Project4/heatsink/serialize.py, Project4/heatsink/site.py, Project4/tests/test_site.py, Project4/tests/test_results_schema.py, and Project4/coordination/handoffs/agent-4.md. Solver, optimizer, configuration, truth, approvals, and workflow files are read-only. Report out-of-scope defects instead of editing them.

Make Project4/site/assets/results.json the sole numerical source for displayed report tables, panels, and geometry. Complete every required report section: summary, formulation, analysis, assumptions, verification, adjoint derivation, sensitivity checks, optimization, nonlinear comparison, results, both bonus sections, limitations, references, and AI-use statement pending final human wording review. Complete all eight viewer requirements: initial/optimized synchronized cameras, true extruded 3D geometry with disclosed exaggeration, sequential temperature colors and color bar, non-color limit markers, mapped field, optimization animation, hover/click inspection, and complete pass/fail panels. Ensure responsive operation around 390 px width and reasonable load/render time.

Success means schema/site tests pass, no displayed numerical result is manually copied, formulas render, viewer JavaScript passes node --check, the static site builds, and desktop plus phone-width visual QA is documented with screenshots or an explicit inspection log. Run the full Project4 suite and git diff --check. Record commands/results, data assumptions, commit, and issues in agent-4.md. Commit/push only agent/report-viewer and open a linked PR; do not merge, enable Pages, change settings, submit links, or push main. Continue until review-ready or genuinely blocked.
```

## Agent 5 — Integration and rubric audit

```text
/goal Integrate and audit Project 4 for a reproducible 110/100 submission, without performing maintainer-only merges or submissions.

You are Agent 5 ([AGENT/TEAMMATE NAME]), the integration agent in a five-agent collaboration. Work in https://github.com/lucasszokol/DesOptCCLP. Pull current main and read AGENTS.md, all Project4/coordination files, Project4/SPECIFICATION.md, Project4/RUBRIC_AUDIT.md, the project brief, and the four specialist issue/PR threads.

Confirm Project4/approvals.yaml and Project4/tests/benchmark_truth.yaml satisfy the human gate. If incomplete, stop and state the exact human action required. Never derive or alter benchmark truth. Create/update issue "[P4-A5] Integration and 110-point audit" and branch agent/integration-audit from current main.

Your exclusive write scope is Project4/heatsink/run_all.py, gates.py, config.py, Project4/config.yaml, Project4/requirements.txt, Project4/README.md, Project4/RUBRIC_AUDIT.md, .github/workflows/project4-pages.yml, Project4/coordination/, and Project4/coordination/handoffs/agent-5.md. Do not edit specialist-owned files. Begin simultaneously by auditing the baseline, reproducibility path, schema, workflow, and rubric mapping. Review Agents 1–4 PRs and leave concrete comments for failures or missing evidence. Do not copy unreviewed work between branches and do not merge their PRs. After the maintainer merges accepted specialist PRs into main, update your branch from main and perform final integration.

Make one documented command regenerate verification, sensitivity evidence, optimization data, plots/tables, and canonical results.json from a clean environment. Enforce gates so a graded run cannot silently proceed without human approvals. Audit all 100 base points and separately demonstrate the +5 nonlinear Newton and +5 topology bonuses with links to generated evidence. Run the clean reproduction command, full tests, schema checks, static-site build, node syntax check, and git diff --check. Report any mismatch honestly; never fill missing evidence with claims.

Success means the reproduction command passes, final designs are feasible, all rubric rows link to concrete artifacts, the site consumes canonical data, and remaining human-only actions are an explicit short checklist: review AI statement, approve/merge PRs, enable Pages, verify the private-window live site, and submit URLs to Canvas. Document commands/results, reviewed PR SHAs, risks, commit, and unresolved items in agent-5.md. Commit/push only agent/integration-audit and open a linked integration PR. Do not merge, change repository settings, enable Pages, or submit Canvas links without Lucas's explicit action-time approval. Continue until the integration PR is review-ready or a genuine blocker is documented.
```

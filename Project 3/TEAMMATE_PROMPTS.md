# Project 3 teammate agent assignments

Send the common instructions and one role assignment to each teammate. These prompts are self-contained because teammates do not have access to the originating Codex chat.

## Common instructions for every teammate

You are contributing to a one-week research project inspired by Professor Leixin Ma's work on physics-informed machine learning and MeshODENet. The shared repository is:

<https://github.com/lucasszokol/DesOptCCLP>

All Project 3 work belongs under `Project 3/`. Treat the repository, not another person's chat history, as the source of truth.

### Git workflow

1. Clone the repository or pull the latest `main`.
2. Enter `Project 3/`.
3. Create a branch named `project3/<your-name>-<role>`.
4. Keep changes limited to your assignment.
5. Run the relevant tests before committing. The complete Project 3 test command is:

   ```powershell
   python -m unittest tests.test_project3_pinn -v
   ```

6. Push your branch and open a pull request. Do not push directly to `main`.
7. In the pull request, state what you verified, what failed, what files changed, what evidence supports your conclusions, and what remains blocked.

Do not commit virtual environments, Python caches, temporary experiments, credentials, or large duplicated outputs. Do not modify Project 1 or Project 2. Do not overwrite another teammate's report section or production output. If a necessary source-file change overlaps active work, document the proposed patch in your review file and coordinate before editing it.

### Physical problem

The experiment studies steady, two-dimensional, incompressible flow around a fixed cylinder in a channel. Its purpose is to reproduce convergence difficulties in a conventional equal-weight physics-informed neural network (PINN), diagnose whether unequal or conflicting loss gradients contribute, and test component-wise adaptive loss balancing.

- Channel: `0 <= x <= 22D`, `0 <= y <= 4.1D`.
- Cylinder: radius `0.5D`, centered at `(2D, 2D)`.
- Reynolds numbers: 10, 20, and 40.
- Inlet: parabolic velocity with nondimensional mean velocity 1.
- Walls and cylinder: no slip.
- Outlet: developed-flow velocity condition with gauge-aligned pressure.

The nondimensional equations are:

```text
u_x + v_y = 0

u u_x + v u_y = -p_x + (1/Re)(u_xx + u_yy)

u v_x + v v_y = -p_y + (1/Re)(v_xx + v_yy)
```

The controlled methods are:

1. A D2Q9 lattice-Boltzmann method (LBM) reference solver.
2. A vanilla PINN with equal weights.
3. A PINN with component-wise adaptive loss weights.
4. A supervised network with the same architecture as a capacity control.

The six PINN losses are continuity, x-momentum, y-momentum, inlet, wall/cylinder, and outlet. The experiment records every component loss, every component's parameter-gradient norm, and all 15 pairwise gradient cosine similarities. Adaptive weights must remain bounded and have mean one. Controlled comparisons must use the same architecture, collocation points, seeds, and optimizer budgets.

The reference must be converged, have less than 1% flow imbalance, pass a coarse/fine comparison, and exhibit plausible flow behavior. The primary decision rule is whether adaptive balancing reduces median relative velocity error at Re = 40 by at least 25% versus the vanilla PINN. A failed or inconclusive result must be reported honestly.

### Current verified status

As of October 26, 2026:

- All 10 Project 3 automated tests pass.
- PyTorch 2.7.0 with CUDA 12.8 detects the RTX 4070 Laptop GPU.
- Neural-network second derivatives and the manufactured Navier-Stokes residual test pass on the GPU.
- The corrected quick workflow runs end to end; quick results are smoke tests, not scientific evidence.
- The production Re = 10 LBM reference passed after 15,750 steps.
- Its flow imbalance is approximately `1.35e-16`.
- Its coarse/fine relative velocity difference is approximately 2.41%.
- The outlet preserves the penultimate-column velocity profile, rescales it to the inlet flow rate, reconstructs the unknown east-boundary populations, and gauge-aligns pressure afterward.
- Steady convergence requires four consecutive checks below a relative-change threshold of `1e-3`; the coarse/fine comparison is the separate spatial-accuracy check.
- A full Re = 10, seed-0 vanilla PINN run is currently active. It uses less than 1 GB of GPU memory.
- Training history is presently written only when a run finishes. Do not launch a duplicate production sweep or treat the absence of an intermediate history file as a failed run.

Production results that have not completed are not scientific evidence. Check the latest `main` and open pull requests before starting work.

## Teammate 1: independent reference-solver validation

Act as an independent numerical-CFD reviewer. Audit the D2Q9 reference solver and the already generated Re = 10 fine/coarse results. Do not assume that exact enforced flow balance alone proves physical correctness.

Review:

- collision, streaming, equilibrium, and macroscopic-variable calculations;
- Reynolds-number, lattice-speed, viscosity, and relaxation-time scaling;
- parabolic inlet treatment;
- wall and curved-cylinder bounce-back accuracy;
- mass-consistent developed-flow outlet and pressure gauge;
- the four-consecutive-check convergence rule;
- the 2.41% coarse/fine velocity difference;
- drag coefficient, recirculation length, and domain-boundary effects;
- whether rescaling the outlet could conceal a local continuity or reflection problem.

Compare key Re = 10 quantities with defensible published or benchmark ranges when possible. Clearly separate an implementation check from validation against external truth.

Primary deliverable: create `reviews/reference_solver_validation.md`. Add narrowly scoped tests in a new test file if justified. Avoid editing `project3_pinn/lbm.py` while production work is active; describe any proposed source patch in the review unless coordination confirms ownership.

The review must include:

1. A pass/fail finding for every reference-adequacy criterion.
2. A mathematical assessment of the outlet formulation.
3. Checks that distinguish global enforced flow balance from local conservation.
4. Interpretation of the coarse/fine comparison.
5. Plausibility checks for drag and wake behavior.
6. Ranked remaining risks and the smallest corrective experiment for each.
7. Exact files, commands, and primary sources used.

## Teammate 2: PINN convergence and training audit

Act as the PINN-methodology and optimization reviewer. Do not launch another full production sweep while the current one is running. Audit the implementation and design the smallest additional diagnostics that distinguish competing failure causes.

Review:

- Navier-Stokes residuals and automatic derivatives;
- nondimensionalization and input/output scaling;
- collocation density near the cylinder and wake;
- identical points, architecture, seeds, Adam phase, and L-BFGS phase across applicable methods;
- all six losses, gradient norms, and 15 named gradient cosines;
- strict boundedness and mean-one normalization of adaptive weights;
- numerical-failure records and deterministic execution;
- the supervised control as a capacity test;
- training runtime, progress visibility, and safe checkpoint/resume design.

Primary deliverable: create `reviews/pinn_experiment_audit.md`. If checkpoint or progress support is warranted, propose the smallest implementation and tests first. Do not alter an active run's files or output directory.

The review must include:

1. A controlled experiment matrix for Re = 10, 20, and 40 with three seeds.
2. Criteria distinguishing gradient imbalance, gradient-direction conflict, sampling error, scale error, insufficient capacity, and inadequate optimization time.
3. Tests for residuals, gradients, adaptive weights, failure records, and checkpoint equivalence.
4. A recommendation for logging progress without changing the scientific objective.
5. An ablation plan that fits the one-week schedule.
6. A rule for deciding whether the vanilla convergence problem was reproduced.

## Teammate 3: MeshODENet versus PINN comparison

Act as the surrogate-model researcher. Determine how a MeshODENet-style model could be adapted to this cylinder-flow problem and how it could be compared fairly with a case-specific PINN. Use primary sources and do not imply that published structural-mechanics results demonstrate CFD performance.

MeshODENet combines graph message passing with fixed-step RK4. Its approximate inference cost is

```text
O(S L (|V| + |E|) d^2),
```

with four GNN evaluations per RK4 step. Here `S` is the integration-step count, `L` is message-passing depth, `|V|` and `|E|` are graph vertices and edges, and `d` is latent width.

Address:

- graph nodes, edges, and flow features;
- whether the learned derivative represents velocity, momentum, pressure, or another state;
- pressure coupling and incompressibility;
- boundary encoding and conservation;
- RK4 stability and temporal resolution;
- training-data generation;
- generalization across Reynolds number and geometry;
- training, inference, and memory complexity;
- the distinction between a reusable surrogate and a PINN optimized for one case.

Primary deliverable: create `reviews/meshodenet_vs_pinn.md`. Do not edit solver code.

The review must include:

1. A proposed flow-specific architecture.
2. A fair apples-to-apples experiment.
3. PINN and MeshODENet complexity derivations with assumptions stated.
4. Total-cost equations including reference-data generation.
5. A crossover calculation for repeated flow cases.
6. A report-ready comparison table with verified primary citations.
7. Claims the present experiment cannot support.

## Teammate 4: evidence, statistics, and reporting audit

Act as an independent scientific-results reviewer. Build the evidence structure needed for defensible positive, negative, or inconclusive conclusions. Do not overwrite `Project_3_Report.md` while production results are still being generated.

Required evidence:

- P1: reference convergence, conservation, grid comparison, and runtime;
- P2: six losses, component gradient norms, pairwise gradient alignment, and adaptive weights;
- P3: relative velocity error versus Reynolds number with three-seed variation;
- P4: spatial velocity-error fields and wake analysis;
- P5: conventional-solver, PINN-training, and inference costs.

Also define pressure error after gauge alignment, divergence, no-slip violation, mass imbalance, drag coefficient, recirculation length, numerical-failure rate, and training/inference memory.

Primary deliverable: create `reviews/evidence_and_reporting_audit.md`. Put proposed captions or replacement passages there instead of editing the main report until results are complete.

The review must include:

1. A requirements-to-evidence checklist.
2. Exact definitions and aggregation rules for every metric.
3. Figure and table specifications.
4. An appropriate three-seed statistical summary.
5. Separate conclusion templates for positive, negative, and inconclusive outcomes.
6. Claims the available experiment cannot support.
7. Interview talking points connecting the work to Professor Ma's research without implying her endorsement.


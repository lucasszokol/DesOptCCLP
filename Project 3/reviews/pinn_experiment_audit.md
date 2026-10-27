# PINN convergence and training audit

**Role:** Teammate 2, PINN methodology and optimization reviewer
**Audit date:** October 26, 2026
**Code reviewed:** commit `713111f` on branch `project3/teammate2-pinn-audit`
**Decision threshold:** The assignment fixes the meaningful-improvement threshold at 25% for the median relative velocity error at Reynolds number 40. This audit does not change that threshold or introduce an unapproved numerical convergence threshold.

## Executive finding

The implementation is suitable for a controlled smoke test and contains the main ingredients required for the planned experiment. The steady Navier–Stokes residuals use automatic first and second derivatives correctly. Vanilla and balanced runs with the same Reynolds number and seed receive the same initial network parameters, point pools, batch-index stream, architecture, Adam budget, and L-BFGS budget. The adaptive weights are projected onto the configured bounds and normalized to have mean one for finite component-gradient norms.

The committed evidence is not sufficient for a scientific conclusion. The repository contains only the production Reynolds number 10 reference, one coarse-grid comparison, and quick smoke-test neural-network outputs. It contains no completed production PINN run. The active production process mentioned in `TEAMMATE_PROMPTS.md` is outside the committed checkout, so its state, command line, and intermediate values cannot be independently verified here. I did not launch a duplicate production sweep.

The most important methodology gaps are:

1. A run writes its history, final model, and training metadata only after all optimization finishes. A long run therefore has no durable progress record and cannot resume after interruption.
2. The L-BFGS phase records no loss components, component-gradient norms, gradient cosines, closure-evaluation count, or phase runtime. The final field can change during L-BFGS while the training history still ends at the last Adam log point.
3. `gradient_diagnostics` omits a named cosine when either gradient norm is at most `1e-20`. The experiment requires all 15 named pairs. An undefined cosine should remain present with an explicit non-finite value and a reason flag.
4. Adaptive-weight updates do not reject non-finite gradient norms before projection. A non-finite norm can propagate into all weights.
5. The sampling design oversamples a broad wake box but has no dedicated fluid points close to the cylinder, no boundary-layer distance strata, and no independent residual-validation point set. Sampling error therefore cannot be separated from optimization error using the present outputs alone.
6. The saved `model.pt` file is treated as proof that a run is complete without checking configuration identity or the presence of history, training metadata, and evaluation files. This behavior is not a safe resume mechanism.

The smallest safe next change is progress logging plus an Adam-phase checkpoint written at the already configured `log_every` interval. That change should be implemented and tested in a separate change after the active run finishes. It does not change the objective, point sequence, optimizer budget, or scientific decision rule.

## 1. Audit scope and evidence

### Files inspected

- [`project3_pinn/pinn.py`](../project3_pinn/pinn.py): network, residuals, losses, diagnostics, adaptive weights, training, failure records, and evaluation.
- [`project3_pinn/geometry.py`](../project3_pinn/geometry.py): loss names and point sampling.
- [`project3_pinn/config.py`](../project3_pinn/config.py): production and quick configurations.
- [`project3_pinn/cli.py`](../project3_pinn/cli.py): command construction and experiment order.
- [`tests/test_project3_pinn.py`](../tests/test_project3_pinn.py): current ten automated tests.
- [`project3_pinn/lbm.py`](../project3_pinn/lbm.py): reference scaling used by the supervised control and evaluation.
- Committed production reference metadata and committed quick-run histories, checkpoints, training metadata, and evaluation summaries.
- Course lecture notes on gradients, curvature, ill-conditioning, Adam, stochastic gradients, L-BFGS, line search, and deterministic project handoff.

### Evidence limitation

The current production configuration artifact lists only Reynolds number 10, and `project3_results/` contains no `runs/` directory. Consequently, this audit verifies implementation structure and smoke-test artifacts, not production convergence behavior. Quick-mode errors are not scientific evidence.

## 2. Requirement-by-requirement findings

| Requirement | Finding | Evidence and implication |
|---|---|---|
| Navier–Stokes residuals and automatic derivatives | Pass for the implemented equations | `navier_stokes_residual` differentiates $u$, $v$, and $p$ with respect to physical nondimensional coordinates and forms continuity plus both momentum residuals. The manufactured-field test checks first and second derivatives. |
| Nondimensionalization and input scaling | Pass with a validation gap | Coordinates use cylinder diameters, velocity uses the inlet mean velocity, viscosity enters as $1/Re$, and LBM pressure is divided by $3U_{\mathrm{lattice}}^2$, which is consistent with the D2Q9 pressure scale. The network maps each input coordinate to $[-1,1]$; automatic differentiation includes that map through the chain rule. There is no output scaling or scale-sensitivity diagnostic. |
| Collocation density near the cylinder and wake | Partial | One quarter of the interior pool comes from $1.25\le x\le8$, $0.25\le y\le3.85$; the remaining points are global. This increases wake density, but it does not create a near-cylinder fluid annulus or distance-based strata. Cylinder no-slip uses approximately one third of `boundary_points`. |
| Identical controlled conditions | Pass for vanilla versus balanced | Reinitializing with the same seed reproduces model parameters. Point pools and batch generator seeds are identical. Architecture, Adam steps, learning rate, L-BFGS maximum iterations, and precision are common. Only the loss weights differ. |
| Supervised control comparability | Partial | It uses the same architecture, initialization rule, Adam budget, L-BFGS budget, and batch size. Its point set must differ because it draws labeled reference nodes. It fits $(u,v,p)$ with one unscaled mean-square loss, so a poor fit could reflect output scaling as well as capacity. |
| Six losses | Pass with an interpretation caution | The six names are fixed. Inlet and wall losses each sum two scalar mean-square terms; outlet sums three. Equal top-level weights therefore do not mean equal weighting of every scalar boundary condition. |
| Six gradient norms and 15 named cosines | Partial | All six norms are computed at diagnostic steps. All 15 cosines appear only when every relevant gradient norm exceeds `1e-20`. Missing pairs violate the fixed schema. Diagnostics cover Adam only. |
| Adaptive-weight bounds and mean-one normalization | Pass for finite inputs | `_bounded_mean_one` projects the six positive relative weights into `[0.1,10.0]` and enforces mean one. The exponential moving average is projected again. Non-finite norms are not rejected. |
| Numerical-failure records | Partial | Exceptions create `failure.json` with the exception, traceback, and configuration. The record does not include the phase, last completed step, device, software versions, Git commit, or last durable checkpoint. Supervised loss finiteness is checked after `optimizer.step`, so a non-finite step can modify parameters before failure is raised. |
| Deterministic execution | Partial | Python, NumPy, and PyTorch are seeded; deterministic PyTorch algorithms are requested; cuDNN benchmarking is disabled; a dedicated seeded batch generator is used. The cuBLAS workspace variable is set after PyTorch may already have been imported, and the environment and Git revision are not saved. Cross-device equality is not established. |
| Runtime and memory | Partial | Total completed training time and synchronized inference time are saved. Adam and L-BFGS phase times, L-BFGS closure evaluations, peak CPU memory, and peak CUDA memory are not saved. |
| Progress visibility | Fail | No progress is printed or durably written during training. `history.csv` appears only after the optimizer finishes. |
| Safe checkpoint and resume | Fail | The final checkpoint contains model parameters and final adaptive weights only. It omits optimizer state, current step, random-generator states, partial history, and phase. Any existing `model.pt` causes an immediate return without a configuration-identity check. |

## 3. Mathematical and implementation assessment

### 3.1 Residual equations

For network output $N_\theta(x,y)=(u,v,p)$, the code computes

\[
r_c=u_x+v_y,
\]

\[
r_x=uu_x+vu_y+p_x-\frac{u_{xx}+u_{yy}}{Re},
\qquad
r_y=uv_x+vv_y+p_y-\frac{v_{xx}+v_{yy}}{Re}.
\]

These expressions are algebraically equivalent to the nondimensional equations in the assignment. The input normalization occurs inside the network, while derivatives are requested with respect to the unnormalized tensor `xy`. PyTorch therefore applies the normalization Jacobian automatically. No manual derivative rescaling is missing.

The current manufactured solution $u=x^2$, $v=y^2$, $p=x+y$ checks both first and second derivatives and the signs of the pressure and viscous terms. It does not check mixed dependence, such as $u(x,y)$ with nonzero $u_y$, or the exact boundary-loss formulas. Those cases belong in the proposed tests below.

### 3.2 Boundary losses

The inlet target

\[
u(0,y)=\frac{6y(H-y)}{H^2},\qquad v(0,y)=0
\]

has cross-sectional mean one. The wall/cylinder loss imposes $u=v=0$. The outlet loss imposes $p=0$, $u_x=0$, and $v_x=0$. These conditions match the report's PINN formulation.

The LBM reference gauge aligns the *mean* outlet pressure to zero, whereas the PINN loss imposes zero pressure at each outlet point. Evaluation removes the mean pressure offset before computing pressure error. These are related but not identical pressure conditions. Velocity error remains the primary metric, so this distinction does not invalidate the primary decision, but outlet pressure profiles should be inspected before using pressure error as supporting evidence.

### 3.3 Adaptive weights

Let $g_i=\lVert\nabla_\theta \mathcal L_i\rVert_2$ and $\bar g$ be the arithmetic mean of the six norms. The proposed target before projection is

\[
\widetilde w_i=\frac{\bar g}{\max(g_i,10^{-12})}.
\]

The implementation finds a common scale factor and clips the scaled values to the configured interval. It then forms an exponential moving average with coefficient 0.9 and projects again. For finite norms, the resulting weights remain within the fixed bounds and their arithmetic mean is one.

The method balances component-gradient magnitudes only approximately because clipping and exponential smoothing prevent the equality $w_i g_i=\bar g$ in general. It does not resolve opposing gradient directions. A negative pairwise cosine

\[
c_{ij}=\frac{\nabla\mathcal L_i^\mathsf T\nabla\mathcal L_j}
{\lVert\nabla\mathcal L_i\rVert_2\lVert\nabla\mathcal L_j\rVert_2}
\]

indicates a local directional conflict. When either norm is zero, $c_{ij}$ is undefined and must be recorded as such rather than omitted.

### 3.4 Optimizer schedule

Adam uses stochastic interior batches sampled with replacement from a fixed 30,000-point pool. Boundary points remain fixed and complete at every Adam step. L-BFGS then uses the first 10,000 interior points from that same shuffled pool and all boundary points. Vanilla and balanced runs with the same seed use identical point sequences and identical optimization budgets.

Course notes correctly motivate Adam for large stochastic neural-network objectives and L-BFGS for lower-noise, mildly nonconvex optimization. They also warn that ill-conditioning slows first-order methods and that L-BFGS assumes stable gradients. This implementation reduces sampling noise for L-BFGS by fixing its points, but it does not log the transition or any L-BFGS diagnostics. Therefore the final result cannot presently be connected to an observed Adam plateau, an L-BFGS improvement, or an L-BFGS failure.

## 4. Controlled production experiment matrix

The production matrix contains 27 neural-network runs after three adequate LBM references exist.

| Reynolds number | Vanilla | Balanced | Supervised |
|---:|---|---|---|
| 10 | seeds 0, 1, 2 | seeds 0, 1, 2 | seeds 0, 1, 2 |
| 20 | seeds 0, 1, 2 | seeds 0, 1, 2 | seeds 0, 1, 2 |
| 40 | seeds 0, 1, 2 | seeds 0, 1, 2 | seeds 0, 1, 2 |

For every fixed pair $(Re,s)$:

- Vanilla and balanced must use the same model initialization, point pool, Adam batch-index sequence, architecture, precision, Adam schedule, and L-BFGS schedule.
- Supervised must use the same model architecture, initialization rule, precision, optimizer budgets, and batch size. Its labeled point set is necessarily different and must be saved or reconstructible from the seed.
- Each completed run must record the exact configuration, Git commit, Python version, PyTorch version, CUDA version, device name, and a hash of the reference file used for training or evaluation.
- Analysis must not silently omit failed seeds. A failure remains part of the numerical-failure rate and blocks a three-seed median until the missing result is explicitly reported.

The committed `project3_results/experiment_config.json` describes only Reynolds number 10. Before the 27-run result is analyzed, the final experiment-level configuration must list all three Reynolds numbers, all three methods, and all three seeds.

## 5. Criteria that distinguish competing failure causes

These criteria use paired evidence and avoid a new numerical threshold. Any future absolute residual, stationarity, or error tolerance requires explicit user approval before use.

| Candidate cause | Evidence supporting the cause | Evidence against the cause or pointing elsewhere |
|---|---|---|
| Gradient-magnitude imbalance | Vanilla component-gradient norms remain separated across training; balanced weighted norms become more nearly aligned; the balanced field error and boundary diagnostics improve for paired seeds. | Norms become more nearly aligned but field error does not improve, or imbalance is absent in vanilla. |
| Gradient-direction conflict | Several named cosines remain negative over the same training region, especially for the component that fails to improve; magnitude balancing leaves these negative directions and the field error unchanged. | Cosines are nonnegative while one component still fails, or a sampling change fixes the error without changing alignment. |
| Sampling error | Training-point residuals are lower than residuals on an independently generated, fixed validation set; validation error concentrates near the cylinder or wake; redistributing the same total number of points improves those regions in a controlled ablation. | Training and independent validation residuals agree spatially, and changing only the point distribution does not improve the field. |
| Scale error | Analytic residual tests pass, but a mathematically equivalent input/output reparameterization changes component-gradient ordering and optimization behavior while representing the same physical fields. | Reparameterization leaves the diagnostics and errors unchanged. |
| Insufficient capacity | The supervised network with the same architecture cannot fit the reference velocity field for the same Reynolds number and seed. | The supervised network fits substantially better than the vanilla PINN, showing that the architecture can represent the sampled field. |
| Inadequate optimization time | Continuing from the same state for one additional existing Adam-budget unit reduces independent residuals and field error without changing points, architecture, or loss definition. | Additional steps change neither independent residuals nor field error, or instability grows. |

No single training-loss curve can distinguish these causes. Reference-field error, independent residual validation, component-gradient magnitudes, gradient directions, and the supervised control must be interpreted together.

## 6. Rule for deciding whether the vanilla convergence problem was reproduced

The repository has no user-approved absolute error or stationarity tolerance. It can therefore make a threshold-free **comparative worsening** claim, but it cannot honestly claim absolute nonconvergence from the present specification.

Define $E_V(Re,s)$ as the final relative velocity error of vanilla for seed $s$, and $E_S(Re,s)$ as the corresponding supervised error. Declare that the targeted worsening was reproduced only when all of the following hold:

1. All nine vanilla production runs complete under the fixed common budget, or every numerical failure is retained and the result is labeled inconclusive rather than silently dropped.
2. The three-seed vanilla median satisfies
   \[
   \operatorname{median}_s E_V(10,s)
   <\operatorname{median}_s E_V(20,s)
   <\operatorname{median}_s E_V(40,s).
   \]
3. Every paired seed has $E_V(40,s)>E_V(10,s)$. This prevents a median trend caused by one seed from being described as a general reproduced behavior.
4. Every paired seed has $E_S(40,s)<E_V(40,s)$. Otherwise, insufficient representation capacity remains a viable explanation.
5. Independent residual and boundary diagnostics show that the Reynolds number 40 vanilla error corresponds to unsatisfied equations or boundary conditions, rather than only disagreement with the LBM reference.

If any condition is false, report mixed or inconclusive evidence. This rule does not determine whether balancing succeeded. Balancing succeeds only under the separate fixed 25% median-error rule and the no-slip requirement stated in the assignment.

## 7. Required tests

### 7.1 Residual and boundary tests

1. Extend the manufactured field so both velocity components depend on both coordinates. Compare continuity and both momentum residuals with closed-form values at deterministic points.
2. Use a small analytic model to verify each of the six returned losses independently, including the parabolic inlet and all three outlet terms.
3. Compare automatic derivatives with analytic derivatives before and after the network's coordinate normalization. This directly protects the input-scaling chain rule.
4. Verify that interior training points never lie in the solid and that an independent diagnostic sampler covers prescribed global, near-cylinder, and wake regions without reusing training points.

### 7.2 Gradient diagnostics tests

1. Compare every flattened component gradient with a direct PyTorch calculation on a small model.
2. Require the exact fixed set of 15 cosine keys for every call.
3. Construct a zero-gradient component. Require its affected cosine keys to remain present with `NaN` plus an explicit validity field, while unaffected pairs remain finite.
4. Verify that diagnostic logging consumes no random numbers and leaves final parameters exactly equal to a run with logging disabled.

### 7.3 Adaptive-weight tests

1. Retain the current finite, bounded, mean-one, and repeated-extreme-update tests.
2. Add equal-norm input and require six weights exactly equal to one.
3. Add `NaN`, positive infinity, and negative infinity norms. Require a controlled numerical failure before any optimizer step.
4. Verify deterministic updates for identical old weights and norms.

### 7.4 Failure-record tests

1. Trigger a non-finite Adam loss and require `failure.json` to include phase, last completed step, run identity, configuration hash, and checkpoint path.
2. Trigger a failure during evaluation after training. Preserve the completed training checkpoint and identify evaluation as the failed phase.
3. Verify that a failed run is never mistaken for a completed run because a partial file exists.
4. Verify that resuming with a different configuration or reference hash is rejected.

### 7.5 Checkpoint-equivalence tests

Use a small deterministic CPU fixture. Run the same Adam optimization in two ways: uninterrupted, and interrupted at a configured log point then resumed. Require exact equality of:

- model parameters;
- Adam state;
- adaptive weights;
- next step;
- batch-generator state;
- Python, NumPy, and PyTorch random states;
- emitted history rows and their order.

For L-BFGS, checkpoint at the phase boundary. If interruption occurs inside the single L-BFGS call, restart that phase from its boundary checkpoint. Require the restarted phase to match an uninterrupted L-BFGS phase on the same device with the same fixed points.

## 8. Smallest safe progress and checkpoint design

Do not retrofit this change into an active output directory. Implement it after the active run finishes and verify it first with quick mode in a new output directory.

At every existing `log_every` interval:

1. Print one flushed progress record containing run identity, optimizer phase, completed step, elapsed time, total loss, six component losses, six gradient norms, 15 named cosines with validity flags, six weights, and peak device memory.
2. Append one row to `history.partial.csv`, flush it, and synchronize the file. Rename it to `history.csv` only after the run completes.
3. Write `checkpoint_latest.pt.tmp`, then atomically replace `checkpoint_latest.pt`. The checkpoint must contain the model, Adam state, next step, adaptive weights, history position, batch-generator state, all random states, phase, exact configuration, Git commit, software versions, and reference hash.
4. Write `progress.json.tmp`, then atomically replace `progress.json`. This small file lets a monitor report status without loading a model checkpoint.

Before L-BFGS, write a phase-boundary checkpoint. The current PyTorch call executes the full L-BFGS phase inside one `step` call, so the smallest reliable design restarts L-BFGS from that boundary after interruption. Do not claim mid-L-BFGS resume equivalence unless the implementation exposes and saves its internal iteration state.

The final `model.pt` should continue to mean *completed optimization*. On startup:

- Return immediately only if final model, training metadata, history, and evaluation outputs all exist and their run identities match.
- Resume only from `checkpoint_latest.pt` with an exact configuration and reference-hash match.
- Refuse ambiguous or incompatible partial state instead of overwriting it.

Detached logging and checkpoint serialization must occur after the optimizer step and must not draw random numbers. These changes preserve the scientific objective and point sequence.

## 9. One-week ablation plan

The order below minimizes new training. It starts only after the active production run has finished or moved to a different output directory.

### Day 1: make runs observable and reproducible

- Implement the progress and checkpoint proposal in a separate change.
- Add the tests in Section 7 and run quick mode in a fresh output directory.
- Record exact environment and run identity.

### Days 2–4: complete the predeclared baseline matrix

- Generate adequate references for Reynolds numbers 20 and 40.
- Complete the 27-run matrix without changing architecture, points, seeds, or optimizer budgets.
- Preserve failures. Do not substitute new seeds after inspecting results.

### Day 5: perform zero-retraining diagnostics

- Evaluate every trained network on one fixed, independently generated diagnostic set split into global, near-cylinder, and wake regions.
- Recompute the six residual/boundary quantities and spatial summaries without changing any trained model.
- Separate Adam and L-BFGS evidence using the new phase logs.

### Day 6: run the smallest cause-specific ablations

Use Reynolds number 40 and seed 0 for mechanism diagnosis; do not mix these exploratory results into the predeclared three-seed decision.

1. **Sampling ablation:** keep the total interior-point count and optimizer budget fixed, but redistribute points into explicit global, near-cylinder, and wake strata.
2. **Optimization-time ablation:** continue vanilla from a compatible Adam checkpoint for one additional existing production Adam-budget unit, with points and loss unchanged.
3. **Scale ablation, only if the analytic scale audit indicates a problem:** apply a mathematically equivalent output reparameterization and transform derivatives back to the same physical residuals.

Run one ablation at a time so each comparison changes only one factor. Do not run all three seeds unless the exploratory result warrants a confirmatory experiment and the team approves the added cost.

### Day 7: apply the fixed decision rules

- Apply Section 6 to the vanilla reproduction question.
- Apply the assignment's fixed 25% median-error rule to adaptive balancing.
- Report gradient imbalance, directional conflict, sampling, scale, capacity, and optimization time as supported, unsupported, or unresolved. Do not name a unique root cause unless the controlled evidence excludes the alternatives.

## 10. Ranked risks and recommended actions

1. **Silent loss of a long production run.** Add durable progress and an Adam checkpoint at the existing log interval after the active run finishes.
2. **Final model cannot be connected to optimizer diagnostics.** Log the L-BFGS boundary, final diagnostics, closure evaluations, and phase runtime.
3. **Sampling and optimization failure are confounded.** Add an independent stratified residual-validation set before retraining.
4. **Incomplete cosine schema.** Preserve all 15 names and mark undefined values explicitly.
5. **Non-finite adaptive weights.** Validate all norms and weights before forming or applying the total loss.
6. **Unsafe completed-run detection.** Require complete, matching artifacts rather than the mere presence of `model.pt`.
7. **Weak provenance.** Save software, hardware, Git, configuration, and reference identities with every run.

## 11. Commands used and commands intentionally not used

Inspected source and committed artifacts with read-only repository and file commands. Inspected the local course PowerPoint files as source material. Hardware inspection shows the review machine is an Apple M1 MacBook Air with 8 GB memory and no installed PyTorch package; committed quick-run metadata identifies the production device as an NVIDIA GeForce RTX 4070 Laptop GPU.

I did not run `project3.py train`, `project3.py all`, or any new production experiment. I did not modify `project3_pinn/`, `tests/`, or an existing output directory. Verification results for the documentation branch are recorded in [`handoff.md`](../handoff.md).

# Project 3: Diagnosing PINN Convergence for Cylinder Flow

**Team Optimus Prime**<br>
**Path B: Diagnosis, with an unsuccessful attempted remedy**

## 1. Outreach log

Our team conducted researcher outreach by email, beginning with Dr. Jeonglae Kim. A scheduling conflict led Dr. Kim to recommend Dr. Leixin Ma, whom we subsequently interviewed by Zoom. The full outreach sequence, including the decline and non-response, is recorded below.

| Date | Contact and method | Outcome |
|---|---|---|
| October 12, 2026 | Emailed Dr. Jeonglae Kim | Initial outreach |
| October 15, 2026 | Second response from Dr. Kim | He reported a scheduling conflict and recommended contacting Dr. Leixin Ma |
| October 16, 2026 | Emailed Dr. Leixin Ma and Dr. Pedro Peralta | Dr. Peralta did not respond; Dr. Ma responded the same day and confirmed a Zoom appointment |
| October 19, 2026 | Zoom interview with Dr. Ma | Discussed computational cost, FSI, prior PINN limitations, and machine-learning alternatives |
| October 19, 2026 | Contacted Vivian Oletty in Dr. Ma's group | Requested additional guidance on a suitable project problem |
| October 20, 2026 | Follow-up interview with Vivian Oletty | Confirmed the problem brief and identified fixed-cylinder flow as the appropriate starting case |
| October 28, 2026 | Follow-up with Dr. Ma with results | Sent recommendation memo to Dr. Ma, no response as of project due date |

During the interview, Dr. Ma explained that large-scale finite-element and finite-volume simulations, particularly fluid–structure interaction problems, can require millions of computational nodes and several hours even on supercomputers. She also described PINN convergence and accuracy problems for systems involving multiple PDEs and geometric nonlinearities.

The follow-up interview with Vivian Oletty, which served as confirmation of our problem brief, allowed to identify fluid flow around a stationary circular cylinder as an appropriate starting point, with a moving cylinder and coupled fluid–structure interactions as potential extensions. He also discussed oscillatory dynamics, long-term prediction accuracy, graph neural networks, frequency-domain techniques, and MeshParamNet, which combines graph learning with FFT-based representations and finite-element simulation data to predict structural deformation.

### Selected interview questions and answers

| Question | Interview response |
|---|---|
| What computational challenges limit conventional numerical solvers? | Dr. Ma explained that large-scale finite-element and finite-volume simulations, especially FSI, can require millions of nodes and several hours even on supercomputers. |
| Have PINNs successfully addressed these computational challenges? | Dr. Ma indicated that PINNs have been investigated but often experience convergence and accuracy difficulties for multiple PDEs and geometric nonlinearities. |
| What physical problem would provide a suitable starting point? | Vivian Oletty identified flow around a fixed cylinder, with a moving cylinder as a possible extension. |
| How long might a simulation of the simplified problem take? | Vivian indicated approximately one to two hours, potentially less than one hour depending on the setup. |
| What alternative machine-learning approaches have been explored? | Vivian discussed MeshParamNet, graph neural networks, FFT-based representations, and supervised finite-element data for structural-deformation prediction. |


## 2. Problem brief

### Scientific problem and real-world value

Dr. Ma's work uses finite-element and finite-volume solvers on models with millions of nodes. Individual simulations can require hours even on ASU supercomputers. Design optimization makes this cost more consequential because it requires many forward evaluations. She described difficult PINN convergence, limited accuracy for coupled PDE systems, and stronger practical performance from supervised black-box surrogates.

High-fidelity fluid–structure interaction combines Navier–Stokes flow, nonlinear structural dynamics, moving interfaces, and sometimes remeshing or turbulence closures. The governing physics therefore include fluid momentum and incompressibility, structural dynamics, and kinematic and dynamic coupling conditions at the fluid–structure interface. At high Reynolds numbers, turbulence approximations can introduce additional modeled physics.

### Current solver, cost, and specific challenges

Dr. Ma reported using finite-element and finite-volume methods for structural, fluid, and coupled fluid–structure problems. The main computational difficulties are multimillion-node meshes, large structural deformation, remeshing, coupled nonlinear PDEs, and repeated forward evaluations during design optimization. Individual simulations can require hours even on ASU supercomputers, making broad design searches or parameter studies expensive. For the simplified cylinder problem, Vivian Oletty's meeting notes estimate approximately one to two hours per conventional simulation, potentially less than one hour depending on the setup.

### Prior PINN, surrogate, and neural-operator experience

The interview notes report that standard loss-based PINNs were difficult to converge and insufficiently accurate for her forward multiphysics applications. Her group therefore uses supervised black-box learning where it is more reliable. Dr. Ma's [MeshODENet](https://arxiv.org/abs/2509.18445), developed with Kangzheng Liu, combines graph neural networks with neural ordinary differential equations for repeated structural simulations. It is a supervised, data-driven forward surrogate trained on conventional-solver trajectories, not a PDE-residual PINN.

MeshODENet has been demonstrated on structural mechanics problems, not on the cylinder-flow problem studied here. Therefore, this report treats it as an architectural direction for repeated design evaluations, not as a measured competitor or a demonstrated CFD solution. Vivian Oletty also discussed MeshParamNet, graph neural networks, and frequency-domain representations as related supervised approaches. 

### Researcher review status

Vivian Oletty, a researcher in Professor Ma's group, reviewed and confirmed the problem brief during the October 20, 2026 follow-up interview. He identified flow around a stationary circular cylinder as an appropriate starting point and moving-cylinder FSI as a possible extension. A separate review of the written brief by Dr. Ma is not documented.

## 3. Minimal case formulation

### Path selection and retained difficulty

We selected **Path B: Diagnosis**, with an unsuccessful attempted remedy. The goal is to reproduce the reported forward-PINN training difficulty, separate representation capacity from physics-informed training behavior, and test whether component-wise gradient-magnitude balancing fixes the problem.

### PDE, domain, boundary conditions, and difficulty knob

The nondimensional channel is

$$
\Omega=[0,22]\times[0,4.1]\setminus
\left\{(x,y):(x-2)^2+(y-2)^2\le0.5^2\right\}.
$$

The steady incompressible Navier–Stokes equations are

$$
u_x+v_y=0,
$$

$$
uu_x+vu_y=-p_x+\frac{1}{Re}(u_{xx}+u_{yy}),
$$

$$
uv_x+vv_y=-p_y+\frac{1}{Re}(v_{xx}+v_{yy}).
$$

The inlet has a parabolic velocity profile with unit mean velocity. The channel walls and cylinder use no-slip conditions. The PINN outlet imposes \(p=0\), \(u_x=0\), and \(v_x=0\). Reynolds number \(Re\in\{10,20,40\}\) is the difficulty knob. Because the target PDE is steady, the PINN has no physical time coordinate or initial condition. The LBM reaches the steady field through pseudo-time iteration initialized with the parabolic velocity profile throughout the fluid and unit density.

### What was simplified and why the hard part remains

This is not a fluid–structure interaction simulation. It removes structural dynamics, interface motion, remeshing, three-dimensional flow, turbulence, and uncertain constitutive behavior. It retains nonlinear momentum, incompressibility, an immersed no-slip boundary, competing equation and boundary losses, and increasing convective influence. This makes it a controlled precursor, not a basis for directly extrapolating quantitative conclusions to moving-boundary FSI.

## 4. Experiments

The experiment follows the course [P1–P5 diagnostic kit](https://designinformaticslab.github.io/DesignOptimization2025/project3.html#anchor-pinn-diagnostic-kit) and the Path B requirement to reproduce a failure and separate competing explanations with controlled comparisons.

### 4.1 P1 — Conventional reference and validation status

A D2Q9 LBM supplies numerical comparison fields. The solver uses BGK collision, bounce-back on the walls and stair-step cylinder, a prescribed parabolic inlet, and a developed-flow outlet that copies and rescales the penultimate-column profile to enforce the inlet volume flux. The pressure reconstructed from density is shifted so that mean outlet pressure is zero.

The implemented acceptance checks require four consecutive 250-step velocity-change checks below \(10^{-3}\), endpoint volume-flux imbalance below 1%, and a grid-disagreement measure below 5%. At \(Re=40\), the 16-versus-24-nodes-per-diameter comparison gives a 1.37% relative velocity difference. This is evidence of resolution consistency between those two grids, not a continuum-error bound.

An independent reference audit reached a more limited conclusion:

- the D2Q9 equilibrium, collision, streaming, and stationary bounce-back operations pass implementation tests;
- the recorded endpoint volume-flux balance is imposed by the outlet and is not an independent mass-conservation check;
- only \(u\) enters the stopping rule, so stationarity of \(v\), density, pressure, drag, and total mass was not established;
- the saved \(x\)- and \(y\)-coordinate spacings differ by about 0.606%, and stair-step bounce-back does not establish accuracy on the true circular boundary;
- a recomputed \(Re=10\) section-volume-flux departure reaches about 1.05%, despite near-zero endpoint imbalance;
- no matched external solution establishes the absolute accuracy of the reported pressure, drag, or recirculation length.

Accordingly, the reference fields are adequate for a provisional internal comparison under the team's implemented gates, but full physical reference adequacy remains unresolved. All errors below should be read as errors relative to this numerical reference.

Reported reference outputs are:

| Re | Steps | Reported runtime | Drag coefficient | Recirculation length |
|---:|---:|---:|---:|---:|
| 10 | 15,750 | 289.4 s | 9.06 | 0.188 D |
| 20 | 20,500 | 357.8 s | 5.98 | 0.813 D |
| 40 | 26,500 | 370.8 s | 4.35 | 1.875 D |

The drag and recirculation values are diagnostics from the current discretization, not externally validated benchmark values.

### 4.2 Controlled neural-network design and P2 method

All neural comparisons use a five-hidden-layer multilayer perceptron with 64 `tanh` neurons per layer and outputs \(u,v,p\). Coordinates are normalized internally. The production configuration uses a fixed pool of 30,000 interior points, interior batches of 4,096 points, 768 points per boundary group, 12,000 Adam steps at learning rate \(10^{-3}\), and up to 300 L-BFGS iterations. Training uses 32-bit floating point. Three seeds are run for each method and Reynolds number.

The vanilla objective is

$$
\mathcal L=\mathcal L_c+\mathcal L_x+\mathcal L_y+
\mathcal L_{in}+\mathcal L_{wall}+\mathcal L_{out}.
$$

The balanced model uses

$$
\mathcal L=\sum_i w_i\mathcal L_i,
\qquad
w_i^*\propto\frac{\overline{\|g\|}}
{\|\nabla_\theta\mathcal L_i\|+\epsilon}.
$$

Weights are updated every 100 Adam steps, smoothed with an exponential moving average coefficient of 0.9, bounded to \([0.1,10]\), and normalized to mean one. This procedure is motivated by the gradient-pathology diagnosis of Wang, Teng, and Perdikaris, but it is not an exact reproduction of their learning-rate annealing algorithm.

The supervised control uses the same architecture and optimizer budgets but fits \(u,v,p\) at 20,000 labeled LBM points. It tests whether the architecture can fit the sampled reference fields. It does not test whether supervised learning alone enforces the PDE or boundary conditions.

For a fixed Reynolds number and seed, vanilla and balanced runs use the same architecture, initialization rule, point pool, stochastic batch sequence, optimizer schedule, and budget. Only the component-weighting rule changes. Logged gradient diagnostics cover Adam; the subsequent L-BFGS phase is not represented in the P2 histories.

### 4.3 Metrics and decision rules

The primary metric is relative velocity error on the reference fluid grid,

$$
E_u=
\frac{\left\|[\hat u-u_{ref},\hat v-v_{ref}]\right\|_2}
{\left\|[u_{ref},v_{ref}]\right\|_2}.
$$

The study also records gauge-aligned pressure error, sampled divergence RMS, combined wall-and-cylinder component RMS velocity, drag, recirculation length, training time, inference time, six loss values, six parameter-gradient norms, six adaptive weights, and 15 pairwise gradient cosines.

The team's declared practical criterion was a 25% reduction in median \(Re=40\) velocity error without worsening no-slip satisfaction. Git history does not establish that this threshold was registered before the completed results were committed, so this report calls it **team-declared**, not preregistered.

Three seeds provide a descriptive median and observed minimum–maximum range. These ranges are not confidence intervals and do not establish population-level robustness or statistical significance.

### 4.4 Path B results

The committed summary contains all 27 expected \((Re,\text{method},\text{seed})\) rows with finite primary error values. The production histories, per-run configurations, predictions, checkpoints, and failure records are not committed, so the complete execution and restart provenance cannot be independently reconstructed from the repository.

#### Primary velocity error

Values are three-seed medians, with the observed seed minimum and maximum in parentheses.

| Re | Vanilla PINN | Component-balanced PINN | Supervised control |
|---:|---:|---:|---:|
| 10 | 0.1708 (0.1377–0.2272) | 0.6915 (0.6792–0.7835) | 0.00518 (0.00498–0.00554) |
| 20 | 0.1886 (0.1260–0.2432) | 0.7005 (0.6853–0.7988) | 0.00523 (0.00497–0.00573) |
| 40 | 0.2238 (0.2193–0.2686) | 0.7277 (0.6919–0.8537) | 0.00562 (0.00526–0.00630) |

#### Was the reported PINN difficulty reproduced?

Yes, in a limited comparative sense. The vanilla median error rises monotonically from 17.1% to 22.4% as Reynolds number increases. Every paired seed also has higher vanilla error at \(Re=40\) than at \(Re=10\). The supervised control fits the same reference velocity labels much more closely at all three Reynolds numbers.

This reproduces poor physics-informed field accuracy under the specified architecture, points, and finite optimizer budget. It does not prove mathematical nonconvergence, failure of every PINN formulation, or error against experimental truth.

At \(Re=40\), the supervised velocity error is about forty times smaller than the vanilla error. This supports the ability of the architecture to fit the sampled velocity field. The conclusion must remain narrow: the supervised median no-slip component RMS is 0.0710 and its divergence RMS is 0.0603, compared with 0.0115 and 0.0412 for vanilla. It is therefore not uniformly more physically accurate.

#### Did adaptive balancing solve the problem?

No. At \(Re=40\), the declared improvement is

$$
1-\frac{0.7277}{0.2238}=-2.251.
$$

The balanced model increases median velocity error by approximately 225%, increases median divergence RMS from 0.0412 to 0.1045, and increases median no-slip component RMS from 0.0115 to 0.0341. It fails both the velocity target and the no-slip guardrail.

#### What mechanism is supported?

The balanced method partially accomplishes its immediate numerical purpose. In the \(Re=40\) median-error runs, the temporal median largest-to-smallest weighted component-gradient ratio is about 19.4 for vanilla and 7.2 for balanced. Nevertheless, field and boundary errors worsen. Gradient-magnitude imbalance is therefore not a sufficient explanation or remedy for the recorded failure.

The minimum observed pairwise gradient cosine reaches approximately \(-0.995\) during logged Adam training, and several adaptive weights approach the lower bound. These observations are consistent with local gradient-direction conflict and weight saturation. They do not show that either effect persisted throughout both optimizer phases or uniquely caused the field error. Sampling, output scaling, optimizer time, spectral bias, the composite loss landscape, and reference error remain alternative or interacting explanations.

The defensible finding is therefore:

> Under the tested objective and budget, inverse-gradient component weighting reduced a gradient-magnitude diagnostic but made the physical and reference-field metrics worse. Gradient-direction conflict is a follow-up hypothesis, not an experimentally verified solution.

### 4.5 P1–P5 diagnostic figures and interpretation

#### P1 — Conventional baseline

![P1 reference accuracy and convergence](project3_results/figures/p1_reference.png)

P1 displays the \(Re=40\) reference speed and the implemented stopping and endpoint-flux diagnostics. The near-zero endpoint imbalance is partly a consequence of the outlet rescaling and should not be interpreted as independent local conservation. The 1.37% 16-versus-24-grid difference and the independent implementation tests provide limited numerical evidence, while the physical-validation concerns in Section 4 remain open.

#### P2 — Loss and gradient diagnostics

![P2 loss, gradient, weight, and alignment histories](project3_results/figures/p2_training_diagnostics.png)

P2 uses the fixed representative \(Re=40\), seed-0 vanilla and balanced runs. It shows Adam histories only. The minimum cosine is an instantaneous worst pair among 15 component pairs; it is not a persistence statistic. Raw production histories are not committed, so the saved figure and summary cannot be fully regenerated from this checkout.

#### P3 — Error versus Reynolds number

![P3 field error versus Reynolds number](project3_results/figures/p3_error_vs_reynolds.png)

P3 shows the median and observed three-seed range, not a confidence interval. Vanilla error worsens with Reynolds number, balanced error is consistently much larger, and supervised label fitting remains near 0.5% relative velocity error.

#### P4 — Error location and spectrum

![P4 spatial and spectral wake error](project3_results/figures/p4_error_location.png)

P4 uses \(Re=40\), seed 0. The maps show large errors in the accelerated shear layers and downstream flow; the balanced error is broader and larger. The two maps use separate automatic color scales, so their colors are not directly comparable. The lower panels are the magnitude of a two-dimensional FFT of wake error speed, with masked values replaced by zero and transverse-frequency magnitudes averaged. They are spatial diagnostic summaries, not temporal spectra or a controlled proof of spectral bias.

#### P5 — Cost

![P5 training, inference, and conventional-solver cost](project3_results/figures/p5_cost.png)

At \(Re=40\), median recorded training times are approximately 478.4 s for vanilla, 476.0 s for balanced, and 79.3 s for the supervised control. The reported LBM solve time is 370.8 s. Median full-grid inference times are approximately 0.00313 s, 0.00297 s, and 0.00445 s, respectively, for 22,745 evaluation points.

The neural runs used an NVIDIA RTX 4070 Laptop GPU. The LBM CPU model was not recorded. The existing timings do not separate setup, Adam, L-BFGS, or data-generation costs; inference is a synchronized single pass rather than a warmed repeated benchmark; peak memory was not recorded. Pointwise inference speed does not imply a design-sweep speedup because the PINN is retrained for each condition.

## 5. Recommendation memo

**To:** Professor Leixin Ma<br>
**From:** Team Optimus Prime<br>
**Subject:** Diagnosing loss-based PINN convergence on a forward-flow precursor

**Confidence:** We have moderate confidence in the recorded negative comparison between equal-weight and adaptively balanced training under the tested setup. We have lower confidence in the absolute CFD errors and in any unique causal explanation because the numerical reference and mechanism evidence remain incomplete.

We reproduced worsening field accuracy for an equal-weight, per-instance forward PINN as Reynolds number increased. The same architecture fit numerical velocity labels much more closely, showing that label-field representation is not the primary limitation. However, inverse-gradient loss balancing made velocity, divergence, and no-slip metrics worse. It should not be adopted as a solution based on this experiment.

We recommend against replacing a mature forward solver with this per-instance PINN formulation. For repeated design evaluations, a supervised graph surrogate or neural operator has a more appropriate amortized structure, but this project did not implement or measure a MeshODENet-style fluid model. Any such surrogate must include CFD data-generation cost and demonstrate generalization, conservation, boundary accuracy, and total break-even cost.

The smallest useful next PINN study is a controlled \(Re=40\) experiment that changes one suspected mechanism at a time: conflict-aware gradient projection, independent near-cylinder residual sampling, or additional optimization time. It should use a better-validated conventional reference and retain the supervised label-fitting control. A successful follow-up must improve the field error without degrading separate cylinder and channel-wall boundary metrics.

The standalone one-page version is available in [`Leixin_Ma_Recommendation_Memo.md`](Leixin_Ma_Recommendation_Memo.md). 


## 6. Assumptions and limitations

The minimal experiment chosen is a barebones fluid mechanics problem that does not encapsulate the complexities of 3D flow or fluid-structure interaction. Therefore, several assumptions were needed for this PINN analysis. The largest assumption is that the 2D fixed cylinder in flow is an adequate representation of fluid dynamics, and successes or failures with analyzing this flow can be extrapolated to more complicated scenarios given more training data and time. Another assumption is that the addition of structural mechanics, along with the interaction between those structural mechanics and fluid mechanics, is simply another layer of physics that a more refined PINN can handle while keeping the underlying theory and structure of the PINN used for the 2D fixed cylinder in flow. This leads to the largest limitation of this experiment: the findings are only as relevant as the correlation between the simplified experiment and more complicated experiments. More research would be required to find how transferrable this experiment is to more complex scenarios.

## Appendix A. Reproducibility and evidence record

The implementation, configuration, commands, and primary tests are documented in [`PROJECT3_README.md`](PROJECT3_README.md). The literature basis is documented in [`Project_3_Literature_Review.md`](Project_3_Literature_Review.md).

The merged independent reviews are:

- [`reviews/reference_solver_validation.md`](reviews/reference_solver_validation.md): D2Q9 implementation checks and reference-adequacy limitations;
- [`reviews/evidence_and_reporting_audit.md`](reviews/evidence_and_reporting_audit.md): result arithmetic, metric definitions, provenance, and claim limits;
- [`reviews/meshodenet_vs_pinn.md`](reviews/meshodenet_vs_pinn.md): measured PINN costs versus an explicitly hypothetical MeshODENet-style fluid adaptation.

The independent reference-validation suite reports all 16 tests passing in its documented CPU environment. These tests establish implementation properties, not complete physical validation. The relevant commands are:

```powershell
python -m unittest tests.test_project3_pinn -v
python -m unittest tests.test_reference_solver_validation -v
python reviews/check_reference_fields.py
```

The committed `project3_results/analysis/summary.csv`, `decision.json`, reference metadata, and figures support the arithmetic in this report. The missing production run directories prevent a fresh end-to-end regeneration of every result from the repository alone.

## Appendix B. References

1. K. Liu and L. Ma, “MeshODENet: A Graph-Informed Neural Ordinary Differential Equation Neural Network for Simulating Mesh-Based Physical Systems,” *Journal of Applied Mechanics*, 93(5), 051005, 2026. [arXiv:2509.18445](https://arxiv.org/abs/2509.18445)
2. S. Wang, Y. Teng, and P. Perdikaris, “Understanding and mitigating gradient pathologies in physics-informed neural networks,” 2020. [arXiv:2001.04536](https://arxiv.org/abs/2001.04536)
3. A. Farea, S. Khan, R. Daryani, E. C. Ersan, and M. S. Celebi, “Learning Fluid-Structure Interaction with Physics-Informed Machine Learning and Immersed Boundary Methods,” 2025. [arXiv:2505.18565](https://arxiv.org/abs/2505.18565)
4. Y. Ren, “Project 3: PINN/PINO in the Field,” *An Introduction to Optimization for Mechanical Engineers*, 2026. [Course project requirements](https://designinformaticslab.github.io/DesignOptimization2025/project3.html)

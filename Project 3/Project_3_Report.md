# Project 3: Diagnosing PINN Convergence for Cylinder Flow

**Team Optimus Prime**

## Executive summary

Professor Leixin Ma studies machine-learning acceleration of computationally expensive structural and fluid–structure simulations. In our interview, she reported that standard loss-based physics-informed neural networks (PINNs) were difficult to converge for her forward problems and that supervised black-box models were more effective.

We therefore selected Path B/C: reproduce a related convergence failure, diagnose its cause, and test one targeted remedy. The minimal case is steady, incompressible flow around a fixed cylinder at Reynolds numbers 10, 20, and 40. A vanilla PINN uses equal weights for six equation and boundary losses. The proposed comparison balances those six terms using their parameter-gradient norms. A supervised network with the same architecture determines whether failure comes from insufficient representation capacity or from physics-informed optimization.

This report deliberately does not assume that adaptive balancing will work. The criterion is declared before training: the remedy must reduce median velocity-field error by at least 25% at Reynolds number 40 without degrading no-slip satisfaction. Otherwise, the conclusion is that this remedy was insufficient.

## 1. Scientific motivation

High-fidelity fluid–structure interaction combines Navier–Stokes flow, nonlinear structural dynamics, interface conditions, and sometimes moving meshes or turbulence closures. Professor Ma reported simulations with millions of nodes and runtimes of hours even on supercomputers. Design optimization makes the cost more severe because it needs many forward evaluations.

Her [MeshODENet](https://arxiv.org/abs/2509.18445) addresses repeated structural simulations with a graph neural network and neural ordinary differential equation trained on conventional-solver trajectories. It is a data-driven forward surrogate, not a standard PDE-residual PINN. Its success alongside her negative PINN experience motivates this project: determine what fails inside the PINN optimizer before recommending more physics losses.

The fixed cylinder is not fluid–structure interaction. It is the smallest precursor that retains nonlinear flow equations, an immersed no-slip boundary, several competing loss terms, and a meaningful difficulty parameter.

## 2. Mathematical model

The nondimensional channel is

\[
\Omega=[0,22]\times[0,4.1]\setminus
\left\{(x,y):(x-2)^2+(y-2)^2\le0.5^2\right\}.
\]

The steady incompressible Navier–Stokes equations are

\[
u_x+v_y=0,
\]

\[
uu_x+vu_y=-p_x+\frac{1}{Re}(u_{xx}+u_{yy}),
\]

\[
uv_x+vv_y=-p_y+\frac{1}{Re}(v_{xx}+v_{yy}).
\]

The inlet has a parabolic profile with unit mean velocity. The channel walls and cylinder use no-slip conditions. The outlet fixes the pressure gauge with \(p=0\) and uses zero streamwise velocity gradients. Reynolds number \(Re\in\{10,20,40\}\) is the difficulty knob.

## 3. Conventional reference

A D2Q9 lattice-Boltzmann method supplies reference velocity and pressure fields. The solver uses BGK collision, bounce-back on the walls and cylinder, a prescribed parabolic inlet, and a developed-flow outlet that preserves the penultimate-column profile while enforcing the inlet volume flux. The arbitrary pressure constant is shifted so the mean outlet pressure is zero. Steady convergence requires four consecutive 250-step checks below a relative velocity-change tolerance of (10^{-3}). It records convergence history, mass imbalance, runtime, drag, and recirculation length.

Reference fields are withheld from the vanilla and balanced PINNs. They are used only for evaluation and for the supervised capacity control.

## 4. Controlled PINN experiment

All comparisons use a five-hidden-layer multilayer perceptron with 64 `tanh` neurons per layer. Inputs are normalized coordinates and outputs are \((u,v,p)\). Architecture, collocation points, random seeds, optimizer schedule, and training budget are held fixed.

The vanilla objective is

\[
\mathcal L=\mathcal L_c+\mathcal L_x+\mathcal L_y+
\mathcal L_{in}+\mathcal L_{wall}+\mathcal L_{out}.
\]

The balanced model uses

\[
\mathcal L=\sum_i w_i\mathcal L_i,
\qquad
w_i^*\propto\frac{\overline{\|g\|}}{\|\nabla_\theta\mathcal L_i\|+\epsilon}.
\]

Weights are bounded, normalized to mean one, and updated through an exponential moving average. This follows the gradient-pathology diagnosis developed by Wang, Teng, and Perdikaris; adaptive weighting itself is not claimed as new. [Primary source](https://arxiv.org/abs/2001.04536)

Three seeds are run at every Reynolds number. Each run logs all six unweighted losses, weights, parameter-gradient norms, all 15 named pairwise gradient cosine similarities, and their minimum and mean.

## 5. Root-cause logic

Loss imbalance is supported only when all of the following occur:

1. Vanilla component gradient norms differ systematically.
2. The supervised network fits the reference field substantially better than the vanilla PINN.
3. Adaptive weighting reduces the gradient imbalance.
4. The balanced model improves reference-field error without worsening no-slip error.

If the supervised control also performs poorly, the experiment cannot attribute failure only to the physics-informed loss. If adaptive weights equalize gradients without improving the field, gradient magnitude was not the complete root cause; directional conflict, spectral bias, sampling, or convergence to another PDE solution remain candidates.

## 6. Required diagnostics

The analysis command generates:

- **P1:** conventional reference field, solver convergence, runtime, and mass balance;
- **P2:** total loss, individual losses, gradient-norm ratio, and adaptive weights;
- **P3:** median relative velocity error versus Reynolds number with seed range;
- **P4:** pointwise velocity error and wake-region Fourier spectrum;
- **P5:** training, inference, and conventional-solve costs.

It also reports pressure error after gauge alignment, divergence RMS, no-slip RMS, drag coefficient, and recirculation length. Machine-readable conclusions are stored in `project3_results/analysis/decision.json`.

## 7. Results and interpretation

The production results must be generated with:

```powershell
python project3.py all
```

Quick-mode results are pipeline checks and must not be quoted as scientific evidence. The final presentation should insert the generated P1–P5 figures here and report the predeclared decision without changing its threshold after seeing the data.

If the balanced error improvement at \(Re=40\) is at least 25%, the result supports component-wise imbalance as one important mechanism. If not, the correct Path B/C result is that adaptive weighting alone did not repair the convergence failure.

## 8. Recommendation to Professor Ma

A PINN that solves one fixed forward instance should not be presented as a replacement for mature FEA or finite-volume solvers. Even successful balancing must include its training cost. For repeated design evaluations, a PINO, graph neural network, or MeshODENet-style surrogate remains the better architectural target.

The practical next experiment would retain supervised trajectory learning while adding selected conservation, equilibrium, or interface penalties. Full moving-boundary FSI should be attempted only after the fixed-cylinder losses and gradients can be controlled. Recent Eulerian–Lagrangian PINN work provides one candidate architecture for that extension. [FSI study](https://arxiv.org/abs/2505.18565)

## 9. Reproducibility

The implementation, commands, outputs, and tests are documented in [`PROJECT3_README.md`](PROJECT3_README.md). The literature basis and distinction between Professor Ma's physics-guided methods are documented in [`Project_3_Literature_Review.md`](Project_3_Literature_Review.md).

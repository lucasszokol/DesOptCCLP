# Project 3 Literature Review: PINN Convergence and Leixin Ma's Research

## Research question

This project asks whether unequal optimization of the individual terms in a physics-informed neural network (PINN) explains the poor convergence that Professor Leixin Ma reported for forward, coupled physics problems. The experiment first attempts to reproduce the failure with equal loss weights. It then changes only the weighting rule and observes whether convergence and field accuracy improve.

Adaptive weighting is not presented as a new algorithm. The contribution is a controlled, component-level diagnosis on a forward-flow problem chosen to precede Professor Ma's fluid–structure interaction applications.

## Professor Ma's research trajectory

| Work | Method | Physics enters through | Relevance |
|---|---|---|---|
| [Weighted sparse-input neural network for vortex-induced vibration](https://dspace.mit.edu/entities/publication/a32b1bf9-b53d-41f7-85d7-1afe4f2ff337) | Sparse-input supervised network | Prior knowledge constrains feature selection | Early physics-guided ML for fluid–structure response; despite the WSPINN acronym, this is not the standard PDE-residual PINN used in this project. |
| [Deep Spring](https://meetings-archive.aps.org/mar/2023/b14/11) | Inverse-design neural network | Work-energy consistency | Shows physics-informed structure can help inverse design of nonlinear rods. |
| [MeshODENet](https://arxiv.org/abs/2509.18445) | Graph neural network plus neural ODE | Mesh connectivity and continuous-time dynamics | A supervised forward surrogate that avoids direct minimization of all governing-equation residuals. |
| [HGTO](https://arxiv.org/abs/2609.15001) | Graph/hypergraph topology optimization | Differentiable finite-element operations | Relevant to design optimization, but it is not the forward cylinder-flow problem studied here. |

The interview indicated that Professor Ma's high-fidelity targets couple fluid and structural equations, can require remeshing, and may use millions of nodes. She reported that loss-based PINNs were difficult to converge and less accurate than black-box supervised models. The fixed-cylinder case removes moving geometry and structural coupling, but retains nonlinear Navier–Stokes residuals, multiple competing loss terms, no-slip boundaries, and a Reynolds-number difficulty knob.

## University of Pennsylvania work

1. Wang, Teng, and Perdikaris identify numerical stiffness and unbalanced back-propagated gradients between composite PINN losses. They propose gradient-statistics-based learning-rate annealing. [Paper](https://arxiv.org/abs/2001.04536) · [Official code](https://github.com/PredictiveIntelligenceLab/GradientPathologiesPINNs)
2. Wang, Yu, and Perdikaris use the neural tangent kernel to show that PINN loss components can converge at different rates and propose eigenvalue-based adaptive calibration. [Paper](https://arxiv.org/abs/2007.14527) · [Official code](https://github.com/PredictiveIntelligenceLab/PINNsNTK)
3. Wang, Sankaran, Wang, and Perdikaris provide reproducible architecture, sampling, weighting, and optimizer recommendations. Their JAX-PI repository includes Navier–Stokes flow around a cylinder. [Expert guide](https://arxiv.org/abs/2308.08468) · [JAX-PI](https://github.com/PredictiveIntelligenceLab/jaxpi)
4. Wang, Sankaran, and Perdikaris show that full-domain PINNs can violate temporal causality and introduce causal training. This motivates later FSI work but is not tested in the steady benchmark. [Paper and official code](https://github.com/PredictiveIntelligenceLab/CausalPINNs)
5. Wang and collaborators distinguish gradient magnitude imbalance from directional conflict and show why scalar first-order weighting may be insufficient. [Gradient-alignment paper](https://arxiv.org/abs/2502.00604)

## Brown University and Karniadakis-group work

1. Raissi, Perdikaris, and Karniadakis introduced the standard continuous PINN formulation for forward and inverse nonlinear PDE problems. [Paper](https://arxiv.org/abs/1711.10561)
2. Jin, Cai, Li, and Karniadakis developed NSFnets in velocity-pressure and velocity-vorticity forms and studied manual and dynamic weighting for incompressible Navier–Stokes flow. [Paper](https://arxiv.org/abs/2003.06496)
3. Shin, Darbon, and Karniadakis proved consistency for selected linear elliptic and parabolic problems. Their result concerns convergence of minimizers as data increase; it does not guarantee that gradient-based training finds a useful minimizer for nonlinear cylinder flow. [Paper](https://arxiv.org/abs/2004.01806)
4. Yu, Lu, Meng, and Karniadakis add gradients of the PDE residual and combine them with residual-based adaptive refinement. [Paper](https://arxiv.org/abs/2111.02801)
5. Wang and collaborators show that forward Navier–Stokes PINNs can converge to nonphysical solutions at higher Reynolds numbers, meaning a low residual is not sufficient evidence of the desired physical solution. [Paper](https://arxiv.org/abs/2309.06010)

## Closest comparisons

- Xiang and collaborators apply probabilistic self-adaptive loss balancing to steady Kovasznay flow, unsteady cylinder wake, and three-dimensional Beltrami flow. This is the closest prior result and prevents this project from claiming that adaptive cylinder-flow weighting is algorithmically new. [Paper](https://arxiv.org/abs/2104.06217)
- Farea and collaborators use separate Eulerian and Lagrangian networks with immersed-boundary coupling for moving-structure FSI. This is the most direct next step if the fixed-cylinder experiment is successful. [Paper](https://arxiv.org/abs/2505.18565)
- Krishnapriyan and collaborators separate approximation failure from optimization failure by fitting the same architecture directly to reference data. This motivates the supervised capacity control. [Paper](https://arxiv.org/abs/2105.14380)

## Gap addressed by this project

The study does not propose a universal PINN solver. It supplies Professor Ma with a controlled answer to a narrower question:

> When a vanilla forward PINN fails on a cylinder-flow precursor, are the individual physics and boundary losses learning at incompatible rates, and does component-wise gradient balancing improve the actual velocity field rather than merely lowering the weighted training objective?

The answer requires field errors against a conventional reference, not loss curves alone.

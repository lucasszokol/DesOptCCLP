# Recommendation memo

**To:** Professor Leixin Ma  
**From:** Team Optimus Prime  
**Subject:** Diagnosing loss-based PINN convergence on a forward-flow precursor

## Decision addressed

You told us that standard PINNs were difficult to converge for forward multiphysics simulations and that supervised black-box models performed better. We built a controlled fixed-cylinder experiment to determine whether unequal optimization of equation and boundary losses is one cause.

## Experiment

We compare an equal-weight PINN with a component-balanced PINN for steady incompressible flow at Reynolds numbers 10, 20, and 40. The balanced version adjusts six individual losses using their parameter-gradient norms. Both methods use identical networks, points, seeds, and training budgets. A conventional lattice-Boltzmann solution measures actual field error, and a supervised copy of the same network tests whether it has enough representation capacity.

## Result to insert after production runs

- Vanilla median velocity error at \(Re=40\): **[generated result]**
- Balanced median velocity error at \(Re=40\): **[generated result]**
- Relative improvement: **[generated result]**
- Predeclared 25% threshold met: **[yes/no]**
- Evidence supports optimization rather than capacity failure: **[yes/no]**

## Recommendation

The recommendation must follow the measured result:

- If balancing meets the threshold, test the same diagnostic on one coupled or moving-boundary case, but retain a conventional reference and supervised baseline.
- If it does not, do not add more PDE-residual complexity to the current forward surrogate. Prioritize MeshODENet-style supervised graph learning and test only selective conservation or interface regularizers.

In either case, we do not recommend a per-instance PINN as a direct replacement for a mature forward solver. For repeated design optimization, a graph surrogate or neural operator has the more appropriate amortized structure.

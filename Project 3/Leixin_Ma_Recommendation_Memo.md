# Recommendation memo

**To:** Professor Leixin Ma  
**From:** Team Optimus Prime  
**Subject:** Diagnosing loss-based PINN convergence on a forward-flow precursor

## Decision addressed

You told us that standard PINNs were difficult to converge for forward multiphysics simulations and that supervised black-box models performed better. We built a controlled fixed-cylinder experiment to determine whether unequal optimization of equation and boundary losses is one cause.

## Experiment

We compare an equal-weight PINN with a component-balanced PINN for steady incompressible flow at Reynolds numbers 10, 20, and 40. The balanced version adjusts six individual losses using their parameter-gradient norms. Both methods use identical networks, points, seeds, and training budgets. A conventional lattice-Boltzmann solution measures actual field error, and a supervised copy of the same network tests whether it has enough representation capacity.

## Result

- Vanilla median velocity error at \(Re=40\): **22.4%**
- Balanced median velocity error at \(Re=40\): **72.8%**
- Supervised-control median velocity error at \(Re=40\): **0.56%**
- Relative balanced improvement: **-225%**; balancing made the error about 3.25 times larger
- Predeclared 25% threshold met: **No**
- Evidence supports optimization rather than capacity failure: **Yes**

All 27 network runs and all reference checks completed without a rejected seed. Magnitude balancing reduced the effective gradient-norm ratio, but gradient directions remained strongly opposed (minimum cosine near -0.995). It also worsened divergence and no-slip errors. The failure is therefore not explained by gradient magnitude alone.

## Recommendation

Do not add more equally weighted PDE-residual terms to the current forward-solver approach. Prioritize MeshODENet-style supervised graph learning for repeated design evaluations. If physics is added, use selective conservation or interface regularizers around supervised data rather than a fully residual-trained solver.

For a follow-up PINN diagnosis, test a method that addresses gradient direction rather than only magnitude—for example gradient projection, conflict-aware multi-objective optimization, or a second-order method. Retain the conventional reference and supervised-capacity control.

In either case, we do not recommend a per-instance PINN as a direct replacement for a mature forward solver. For repeated design optimization, a graph surrogate or neural operator has the more appropriate amortized structure.

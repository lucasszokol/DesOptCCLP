# Feedback email draft

**Subject:** Follow-up results from our PINN convergence case study

Dear Professor Ma,

Thank you again for discussing your fluid–structure simulation and machine-learning work with us. Based on your experience with difficult PINN convergence, we built a controlled forward-flow case around a fixed cylinder.

We compared a standard equal-weight PINN with a version that balances the individual continuity, momentum, and boundary losses using their gradient magnitudes. We also used a conventional reference solver and a supervised network with the same architecture so that we could distinguish optimization failure from insufficient model capacity.

Our one-page recommendation memo and main diagnostic figures are attached. Our principal result is that the standard PINN showed a clear optimization failure, but component-wise gradient-magnitude balancing did not repair it. At Reynolds number 40, median velocity error increased from 22.4% for the vanilla PINN to 72.8% for the balanced PINN, while the same architecture trained directly on reference data reached 0.56% error. The balanced gradients remained strongly directionally opposed even after their magnitudes became more equal.

As an external plausibility check on the numerical reference, the \(Re=20\) LBM drag and front-to-rear pressure difference are within 7.25% of the official DFG 2D-1 values. Because our outlet condition and cylinder discretization differ from that benchmark, we still treat the reference as provisional rather than exact CFD ground truth.

Our recommendation is therefore to prioritize a supervised MeshODENet-style surrogate for repeated forward evaluations and, if physics regularization is added, use selective conservation or interface terms. A useful PINN follow-up would target gradient-direction conflict rather than adding more residual losses.

We would appreciate any feedback on whether this diagnosis matches the behavior you have seen in larger multiphysics cases and whether a coupled moving-boundary extension would be useful.

Thank you,

Team Optimus Prime

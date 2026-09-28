## 5. Proposed Solution and Demonstration

To remedy the high convergence times, the conjugate gradient descent method is chosen. This family of problems is inherently positive definite because of the argument of the minimum function is a positive curvature quadratic. Because every non-zero displacement stores energy in the strain of the structure, the stiffness matrix (and also reduced stiffness matrix) is positive definite, making the Hessian of the original function positive definite. This family of problems is a perfect fit for conjugate gradient descent. Conjugate gradient descent is a type of gradient descent that combines both the current negative gradient with its previous search direction, which produces K-conjugate directions. While a standard gradient descent search may zigzag or turn around when descending a high curvature function, effectively undoing a lot of its progress, conjugate gradient descent ensures that this zigzag does not occur, which helps the solver not undo progress. 

D4

Plot of convergence curves.
From the convergence curves, it is clear that the conjugate gradient descent converges quicker across all stiffness ratios

The effective rate is defined below, which is the average fraction of energy error retained per iteration. Larger values of this mean that more error is retained per iteration, meaning that smaller values correspond to faster convergence. The reciprocal of this is the average fraction of energy error removed per iteration. This value is taken at the kth iteration where the tolerance of 10-8 is reached. 

Table of convergences and effective rates for GD and CG for R

$$\rho_{\mathrm{eff}}=\left(\frac{\Pi(u_k)-\Pi(u^\star)}{\Pi(u_0)-\Pi(u^\star)}\right)^{1/k}$$

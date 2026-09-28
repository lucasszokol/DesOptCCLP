## 5. Proposed Solution and Demonstration

To remedy the high convergence times, the conjugate gradient descent method is chosen. This family of problems is inherently positive definite because of the argument of the minimum function is a positive curvature quadratic. Because every non-zero displacement stores energy in the strain of the structure, the stiffness matrix (and also reduced stiffness matrix) is positive definite, making the Hessian of the original function positive definite. This family of problems is a perfect fit for conjugate gradient descent. Conjugate gradient descent is a type of gradient descent that combines both the current negative gradient with its previous search direction, which produces K-conjugate directions. While a standard gradient descent search may zigzag or turn around when descending a high curvature function, effectively undoing a lot of its progress, conjugate gradient descent ensures that this zigzag does not occur, which helps the solver not undo progress. To keep comparison fair, Both the gradient descent solver and the conjugate gradient solver will not use Jacobi rescaling for their solution, as it was not used for the initial gradient descent solution for the baseline convergence. Traditional CG starts with residual $r_0=f-Ku_0$ and search direction $p_0=r_0$. It then uses

$$
\alpha_k=\frac{r_k^Tr_k}{p_k^TKp_k},
$$

$$
u_{k+1}=u_k+\alpha_kp_k,
$$

$$
r_{k+1}=r_k-\alpha_kKp_k,
$$

$$
\beta_k=\frac{r_{k+1}^Tr_{k+1}}{r_k^Tr_k},
\qquad
p_{k+1}=r_{k+1}+\beta_kp_k.
$$


## D4

Plot of convergence curves.
From the convergence curves, it is clear that the conjugate gradient descent converges quicker across all stiffness ratios

The effective rate is defined below, which is the average fraction of energy error retained per iteration. Larger values of this mean that more error is retained per iteration, meaning that smaller values correspond to faster convergence. 1 minus this is the fraction of energy error removed. This value is taken at the kth iteration where the tolerance of 10-8 is reached. 

$$\rho_{\mathrm{eff}}=\left(\frac{\Pi(u_k)-\Pi(u^\star)}{\Pi(u_0)-\Pi(u^\star)}\right)^{1/k}$$

<img width="1440" height="864" alt="image" src="https://github.com/user-attachments/assets/77651f93-f498-4e01-b33b-fc2dbfc7780e" />

This graph demonstrates that the energy error removed $(1-\rho_{\mathrm{eff}})$ is very low for gradient descent, and decreases as the stiffness ratio increases. However, for conjugate gradient descent, that energy error removed stays high and relatively constant.

<img width="1440" height="864" alt="image" src="https://github.com/user-attachments/assets/485c8f6a-aa12-461f-b8e2-8f05557a4d2b" />

From this graph, it is evident that the conjugate gradient descent converges much quicker than the gradient descent. This is due to the solver not undoing its progress every step, and instead taking a route that is more "continuous" down to the minimum. 

| $r$ | GD iterations | CG iterations | Iteration speedup | GD $\rho_{\mathrm{eff}}$ | CG $\rho_{\mathrm{eff}}$ |
|---:|---:|---:|---:|
| 1 | 15,168 | 24 | 632 | 0.998786 | 0.297460 |
| 10 | 22,272 | 24 | 928 | 0.999173 | 0.405690 |
| 100 | 128,397 | 26 | 4,938 | 0.999857 | 0.367552 |
| 1,000 | 1,195,856 | 28 | 42,709 | 0.999985 | 0.517642 |
| 10,000 | 11,871,364 | 32 | 370,980 | 0.999998 | 0.464702 |


It is important to note that Newton's method could have been used for this solution as well, as that would remedy the ill-constrained Hessian. However, for larger structures or finite element meshes, that Hessian may grow large, and so it may not be desired to calculate or store that Hessian. 

## 6. Assumptions and Simplifications

## 7. Results from Solver


<img width="1150" height="875" alt="image" src="https://github.com/user-attachments/assets/0798b383-47d8-4ed0-ae8f-120b2eb905d2" />





## 4. Effect on gradient descent

Gradient descent has the following update step for nodal displacement:

$$
u_{k+1}=u_k-\alpha(Ku_k-f),
$$

where $\alpha$ in the initialization $u_0=0$ is calculated as

$$
\alpha=\frac{2}{\lambda_{\max}+\lambda_{\min}},
$$

the optimal fixed step size based on the extreme eigenvalues for a symmetric positive definite matrix such as $K$. Even with this favorable choice, the worst-direction error is reduced by a factor of

$$
\rho=\frac{\kappa-1}{\kappa+1}.
$$

When the condition number is large, $\rho$ approaches one, so each iteration removes only a small fraction of the remaining error. This is why gradient descent converges slowly when the quadratic potential energy surface has a long, narrow shape.

The convergence measure is the fraction of the initial potential energy error that remains:

$$
\frac{\Pi(u_k)-\Pi(u^\star)}{\Pi(u_0)-\Pi(u^\star)}.
$$

The tolerance is set to $10^{-8}$. Instead of calculating each displacement ($u_0,u_1,u_2,\ldots$) from gradient descent one at a time, the code uses the eigenvectors of $K$ to calculate these displacement vectors directly. This avoids performing millions of unnecessary Python loop operations.

| <i>r<i> | Gradient descent iterations to 10<sup>-8</sup> |
|---:|---:|
| 1 | 15,168 |
| 10 | 22,272 |
| 100 | 128,397 |
| 1,000 | 1,195,856 |
| 10,000 | 11,871,364 |

The iteration count increases by nearly three orders of magnitude over the tested stiffness ratios. This is the practical effect of the growing condition number.

## 3. Ill-conditioning mechanism

The structural knob of this project is the axial-rigidity/spring stiffness equivalent ratio

$$
\begin{gather*}
k=\frac{EA}{L}.\\
r=\frac{k_{\max}}{k_{\min}}.
\end{gather*}
$$

A member has a specific Young's Modulus (E), cross sectional area (A), and length (L). The equivalent spring stiffness (k) is found for each member through the equation above. The k matrix shows all equivalent spring stiffness, which will become more varied as more structural members are added as shown by an increase of the ratio r. The tested values are r = 1, 10, 100, 1000, 10000.

The eigenvalues of k measures maximum and minimum stiffness in certain directions. The condition number ($\kappa$) is the ratio of these eigenvalues, as shown:

$$
\kappa=\frac{\lambda_{\max}}{\lambda_{\min}},
$$

The mechanism primer for this project is 'Family A', Multi-scale Physical Parameters. This project is solving for the deflection of a truss structure with the constraint that not all members have the same stiffness. This means that the main constraint of the system is inbuilt as having both stiff and soft members in the full system. Because of this, the hessian eigenvalues span the stiffness ratio. The largest eigenvalue grows in proportion to r, while the smallest eigenvalue does not.

### D2: Intrinsic test using diagonal rescaling

**Diagonal rescaling** uses the diagonal matrix of K and forms

$$
\widehat K=D^{-1/2}KD^{-1/2}.
$$

This gives each displacement coordinate a unit diagonal stiffness and tests whether the large condition number is caused only by different coordinate scales or units. It is also called Jacobi rescaling.

![Condition number versus stiffness ratio]()
**Condition Number v Stiffness Ratio Placeholder**

| r | $\kappa(K)$ | $\kappa(\widehat K)$ |
|---:|---:|---:|
| 1 | $3.30\times10^3$ | $2.01\times10^3$ |
| 10 | $4.86\times10^3$ | $2.63\times10^3$ |
| 100 | $2.81\times10^4$ | $1.49\times10^4$ |
| 1,000 | $2.62\times10^5$ | $1.39\times10^5$ |
| 10,000 | $2.60\times10^6$ | $1.38\times10^6$ |

The rescaled condition number still grows by nearly three orders of magnitude. The reason is structural. After rescaling, stiff-member terms are order one and soft-diagonal terms are order (1/r). The stiff-member network still has shear-like mechanism directions, so the smallest eigenvalues are controlled by the (1/r) soft terms while the largest eigenvalues remain order one. Therefore, diagonal rescaling does not remove the dependence on (r). This satisfies the intrinsic ill-conditioning test.

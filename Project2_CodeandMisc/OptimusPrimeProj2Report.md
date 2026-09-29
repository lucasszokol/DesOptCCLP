# Project 2: Ill-Conditioned Optimization in an Aircraft Spar Truss

**Team Optimus Prime**

This report studies a simplified aircraft spar as both a finite element analysis (FEA) problem and an optimization problem. The purpose is not to design a flight-ready spar. The purpose is to isolate one structural feature, a large difference between member stiffnesses, and show how it creates an ill-conditioned optimization problem.

For more information about the code of this project, please see [`README.md`](README.md). The complete, commented implementation is in [`project2_truss.py`](project2_truss.py). The editable model data is in [`truss_config.py`](truss_config.py). 

## 1. Problem Identification and Motivation

Aircraft spars carry bending and shear loads along a wing. A straight truss member has axial stiffness

$$
k=\frac{EA}{L},
$$

where $E$ is Young's modulus, $A$ is cross-sectional area, and $L$ is member length. Young's modulus measures how strongly a material resists elastic stretching. A large difference in $E$, $A$, or $L$ can create a large difference in member stiffness.

The documented example is a 2D Warren-style truss with 14 nodes. The upper and lower chords and the vertical posts form the stiff member group. The alternating diagonal braces form the soft member group. Both root nodes are fixed. A downward tip load is divided equally between the upper and lower tip nodes.

![Warren truss model](figures/warren_spar.png)

The model has two displacement components at each node: horizontal displacement and vertical displacement. Fixing both components at the two root nodes leaves 24 unknown displacement values.

The model is configurable. A student edits four readable lists in `truss_config.py`:

- `NODES = [(x, y), ...]` gives node coordinates.
- `MEMBERS = [(node_i, node_j, group), ...]` gives connections and assigns each member to the `"soft"` or `"stiff"` group.
- `SUPPORTS = [(node, fix_x, fix_y), ...]` identifies fixed displacement components.
- `LOADS = [(node, force_x, force_y), ...]` gives applied nodal forces.

Node numbers are zero-based list positions. For example, node 0 is the first coordinate in `NODES`. A 7-to-14-node model is recommended for a manually traced picture because it preserves the main load paths without requiring the user to enter and debug approximately 100 nodes and many more connections. The stiffness matrix is assembled from these structural inputs. The user does not enter the stiffness matrix directly.

## 2. Mathematical Formulation

We seek the horizontal and vertical displacements of the truss nodes under a prescribed load. Although this is a structural equilibrium problem, it can also be formulated as a total potential energy minimization problem. This formulation allows us to study how differences in member stiffness affect the behavior of optimization algorithms.

### 2.1 Decision variables and parameters

A decision variable is a quantity whose value is selected by the optimization problem. The member properties $E$, $A$, and $L$, together with the applied force magnitude, are model parameters in this study; they are not decision variables.

The decision variable is

$$
u=[u_{1x},u_{1y},u_{2x},u_{2y},\ldots]^T, -\infty \lt u_i \lt \infty
$$

the vector of unknown nodal displacements. Each of the 14 nodes has two displacement components, giving 28 degrees of freedom. Fixing both root nodes prescribes four of these components as zero, leaving 24 unknown displacements. Therefore, $u\in\mathbb{R}^{24}$, and each candidate vector represents one possible deformed configuration of the truss. The 24 decision variables are continuous real-valued displacements. Under the ANSYS comparison convention, their units are millimeters, and they have no explicit upper or lower bounds.

Material properties and member dimensions are prescribed inputs. This problem determines structural displacements; it does not optimize material selection or member sizing.

### 2.2 Truss finite element

Each truss member is modeled as a straight, linearly elastic element that carries axial force only. Its axial stiffness is

$$
k_e=\frac{EA}{L},
$$

where $E$ is Young’s modulus, $A$ is the cross-sectional area, and $L$ is the original member length. $E$ and $A$ are constant along each member but may differ between members.

#### Member orientation and displacement

For a member connecting nodes $i$ and $j$, define the direction cosines

$$
c=\frac{x_j-x_i}{L},
\qquad
s=\frac{y_j-y_i}{L},
$$

where $(x_i,y_i)$ and $(x_j,y_j)$ are the original nodal coordinates. Equivalently, $c=\cos\theta$ and $s=\sin\theta$, where $\theta$ is the angle between the member and the global horizontal axis.

Each endpoint has a horizontal and a vertical displacement. These four components form the element displacement vector:

$$
u_e=
\begin{bmatrix}
u_{ix}\\
u_{iy}\\
u_{jx}\\
u_{jy}
\end{bmatrix}.
$$

Under the small-displacement assumption, the member’s axial extension is the relative displacement of its endpoints projected along its original axis:

$$
\delta_e=c(u_{jx}-u_{ix})+s(u_{jy}-u_{iy}).
$$

Positive $\delta_e$ indicates elongation, while negative $\delta_e$ indicates shortening. If both endpoints move by the same amount in the same direction, their relative displacement is zero and the member does not stretch.

#### Element strain energy and stiffness matrix

The elastic strain energy stored in the member is

$$
U_e=\frac12 k_e\delta_e^2
=\frac12\frac{EA}{L}\delta_e^2.
$$

To express this energy in terms of the endpoint displacements, write the extension as

$$
\delta_e=b_eu_e,
\qquad
b_e=
\begin{bmatrix}
-c&-s&c&s
\end{bmatrix}.
$$

Substituting into the strain-energy expression gives

$$
U_e
=\frac12u_e^T
\left(\frac{EA}{L}b_e^Tb_e\right)u_e
=\frac12u_e^TK_eu_e.
$$

Therefore, the member stiffness matrix in global coordinates is

$$
K_e=\frac{EA}{L}
\begin{bmatrix}
c^2 & cs & -c^2 & -cs\\
cs & s^2 & -cs & -s^2\\
-c^2 & -cs & c^2 & cs\\
-cs & -s^2 & cs & s^2
\end{bmatrix}.
$$

This matrix relates the four endpoint displacement components to the corresponding internal nodal force components. The factors $c$ and $s$ account for the member’s orientation, allowing the same formulation to represent horizontal, vertical, and diagonal members.

#### Global assembly and boundary conditions

The global stiffness matrix is constructed by adding each member’s stiffness contributions to the rows and columns corresponding to its endpoint displacement coordinates. Members sharing a node contribute to the same nodal equilibrium equations.

The truss has $14$ nodes with two displacement components per node, so the full stiffness matrix is $28\times28$. Both displacement components at each of the two root nodes are fixed at zero. Removing the corresponding four rows and columns applies these boundary conditions and leaves a reduced $24\times24$ stiffness matrix. The corresponding force-vector entries for the root nodes are also removed. 

In the following sections, $K$ denotes this reduced matrix, $u\in\mathbb{R}^{24}$ contains the unknown free-node displacements, and $f\in\mathbb{R}^{24}$ contains the corresponding applied nodal forces. The total strain energy stored in the supported truss is then

$$
U(u)=\frac12u^TKu,
$$

which provides the elastic-energy term in the optimization formulation.

### 2.3 Minimum-potential-energy problem

The equilibrium displacement minimizes total potential energy:

$$
\min_u \Pi(u)=\frac{1}{2}u^T K u-f^T u.
$$

Here, $f$ is the prescribed, displacement-independent reduced external force vector. The total potential energy $\Pi(u)$ is the sum of the elastic strain energy, $\frac12u^TKu$, and the potential energy of the applied loads, $-f^Tu$.

The gradient and Hessian are

$$
\nabla \Pi(u)=Ku-f, \qquad \nabla^2\Pi(u)=K.
$$

The gradient gives the slope of the objective with respect to every displacement. The Hessian is the matrix of second derivatives; here, the Hessian is exactly the stiffness matrix. Setting the gradient to zero gives

$$
Ku^\star=f.
$$

Each element stiffness matrix $K_e$ is symmetric, and assembly and reduction preserve this symmetry. For this supported truss, the computed eigenvalues of the reduced matrix $K$ are all positive, confirming that no rigid-body modes or internal mechanisms remain in the linearized model. Therefore, $K$ is symmetric positive definite, meaning $x^TKx>0$ for every nonzero vector $x$. The objective is consequently an unconstrained strictly convex quadratic, and $u^\star$ is its unique global minimizer.

## 3. Ill-Conditioning Mechanism

The structural knob of this project is the axial-rigidity/spring stiffness equivalent ratio

$$
\begin{gather*}
k=\frac{EA}{L}.\\
r=\frac{k_{\max}}{k_{\min}}.
\end{gather*}
$$

A member has a specific Young's Modulus $E$, cross sectional area $A$, and length $L$. The equivalent spring stiffness $k$ is found for each member through the equation above. The $K$ matrix shows all equivalent spring stiffnesses, which will become more varied as stiffness is varied, resulting in the stiffness ratio $r$ changing. The tested values are $r = 1, 10, 100, 1000, 10000$.

The eigenvalues of $K$ measures maximum and minimum stiffness in certain directions. The condition number $\kappa$ is the ratio of these eigenvalues, as shown:

$$
\kappa=\frac{\lambda_{\max}}{\lambda_{\min}},
$$

The mechanism primer for this project is 'Family A', Multi-scale Physical Parameters. This project is solving for the deflection of a truss structure with not all members have the same stiffness. This means that the main structural feature of the system is inbuilt as having both stiff and soft members in the full system. Because of this, the hessian eigenvalues span the stiffness ratio. The largest eigenvalue grows in proportion to $r$, while the smallest eigenvalue does not.

### D2: Intrinsic test using diagonal rescaling

**Diagonal rescaling** uses the diagonal matrix of $K$ and forms

$$
\widehat K=D^{-1/2}KD^{-1/2}.
$$

This gives each displacement coordinate a unit diagonal stiffness and tests whether the large condition number is caused only by different coordinate scales or units. It is also called Jacobi rescaling.

![Condition number versus stiffness ratio](figures/condition_number_vs_ratio.png)

| $r$ | $\kappa(K)$ | $\kappa(\widehat K)$ |
|---:|---:|---:|
| 1 | $3.30\times10^3$ | $2.01\times10^3$ |
| 10 | $4.86\times10^3$ | $2.63\times10^3$ |
| 100 | $2.81\times10^4$ | $1.49\times10^4$ |
| 1,000 | $2.62\times10^5$ | $1.39\times10^5$ |
| 10,000 | $2.60\times10^6$ | $1.38\times10^6$ |

The rescaled condition number still grows by nearly three orders of magnitude. The reason is structural. After rescaling, stiff-member terms are order one and soft-diagonal terms are order (1/r). The stiff-member network still has shear-like mechanism directions, so the smallest eigenvalues are controlled by the (1/r) soft terms while the largest eigenvalues remain order one. Therefore, diagonal rescaling does not remove the dependence on (r). This satisfies the intrinsic ill-conditioning test.


## 4. Effect of Ill-Conditioning on Gradient Descent

Gradient descent (GD) has the following update step for nodal displacement:

$$
u_{k+1}=u_k-\alpha(Ku_k-f),
$$

where $\alpha$ at $u_0=0$ is calculated as

$$
\alpha=\frac{2}{\lambda_{\max}+\lambda_{\min}},
$$

the optimal fixed step size based on the extreme eigenvalues for a symmetric positive definite matrix such as $K$. Even with this favorable choice, the worst-direction error is reduced by a factor of

$$
\rho=\frac{\kappa-1}{\kappa+1}.
$$

When the condition number is large, $\rho$ approaches one, so each iteration removes only a small fraction of the remaining error. A large condition number means that the quadratic potential energy surface has very different curvature in different displacement directions, producing a long, narrow valley around the minimum. This makes gradient descent converge slowly.


### D1: Eigenvalue spectrum + condition number

The eigenvalue spectrum  is shown in the figure below. From the definition of $\kappa$, at $r=10000$, the original condition number is $2.60\times10^6$. The large spread in eigenvalues resulting in such high $\kappa$ highlights the presence of ill-conditioning. After diagonal rescaling, the condition number decreases to approximately $1.38\times10^6$, but remains large, so the ill-conditioning is not eliminated.

![D1](figures/eigenvalue_spectrum.png)


### D3: Baseline convergence

The convergence behavior of the baseline method – gradient descent – is shown in the figure below. Gradient descent requires $\sim 10^7$ iterations to converge to the desired tolerance of $10^{-8}$, which is very slow. This agrees with what we know about the eigenvalue spectrum and the effects of a large condition number.   

![D3](figures/optimizer_convergence.png)

The convergence measure is the fraction of the initial potential energy error that remains:

$$
\frac{\Pi(u_k)-\Pi(u^\star)}{\Pi(u_0)-\Pi(u^\star)}.
$$

Instead of calculating each displacement ($u_0,u_1,u_2,\ldots$) from gradient descent one at a time, because eigenvector components have a known contraction factor, relative potential energy error can be evaluated at any iteration. This avoids performing millions of unnecessary Python loop operations.

| $r$ | Gradient descent iterations to 10<sup>-8</sup> |
|---:|---:|
| 1 | 15,168 |
| 10 | 22,272 |
| 100 | 128,397 |
| 1,000 | 1,195,856 |
| 10,000 | 11,871,364 |

The iteration count increases by nearly three orders of magnitude over the tested stiffness ratios. This is the practical effect of the growing condition number.

## 5. Proposed Solution and Demonstration

To remedy the high convergence times, the conjugate gradient (CG) descent method is chosen. This reduced stiffness matrix, when fixed-root degrees of freedom are removed, is symmetric positive definite because the supports remove rigid-body motion, the member layout has no remaining mechanism, and all member stiffnesses are positive. Because every non-zero displacement stores energy in the strain of the structure, the stiffness matrix (and also reduced stiffness matrix) is positive definite, making the Hessian of the original function positive definite. This family of problems is a perfect fit for conjugate gradient. Conjugate gradient is a type of gradient descent that combines both the current negative gradient with its previous search direction, which produces K-conjugate directions. Explicitly, the search directions satisfy $p_i^TKP_j = 0 (i\neq j)$. While a standard gradient descent search may zigzag or turn around when descending a high curvature function, effectively undoing a lot of its progress, conjugate gradient ensures that this zigzag does not occur, which helps the solver not undo progress. To keep comparison fair, Both the gradient descent solver and the conjugate gradient solver will not use Jacobi rescaling for their solution, as it was not used for the initial gradient descent solution for the baseline convergence. Traditional CG starts with residual $r_0=f-Ku_0$ and search direction $p_0=r_0$. It then uses

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


### D4: The fix

Plot of convergence curves is shown later in this section.
From the convergence curves, it is clear that the conjugate gradient converges quicker across all stiffness ratios

The effective rate is defined below, which is the average fraction of energy error retained per iteration. Larger values of this mean that more error is retained per iteration, meaning that smaller values correspond to faster convergence. 1 minus this is the fraction of energy error removed. This value is taken at the kth iteration where the tolerance of $10^{-8}$ is reached. 

$$\rho_{\mathrm{eff}}=\left(\frac{\Pi(u_k)-\Pi(u^\star)}{\Pi(u_0)-\Pi(u^\star)}\right)^{1/k}$$

![Effective Rate vs Stiffness Ratio](figures/effective_rate_vs_ratio.png)

The figure above demonstrates that the energy error removed $(1-\rho_{\mathrm{eff}})$ is very low for gradient descent, and decreases as the stiffness ratio increases. However, for conjugate gradient, that energy error removed stays high and relatively constant.

![Optimizer Convergence](figures/optimizer_convergence.png)

From the figure above, it is evident that the conjugate gradient converges much quicker than the gradient descent. This is due to the solver not undoing its progress every step, and instead taking a route that is more "continuous" down to the minimum. 

| <i>r<i> | GD iterations | CG iterations | Iteration speedup | GD $\rho_{\mathrm{eff}}$ | CG $\rho_{\mathrm{eff}}$ |
|---:|---:|---:|---:|---:|---:|
| 1 | 15,168 | 24 | 632 | 0.998786 | 0.297460 |
| 10 | 22,272 | 24 | 928 | 0.999173 | 0.405690 |
| 100 | 128,397 | 26 | 4,938 | 0.999857 | 0.367552 |
| 1,000 | 1,195,856 | 28 | 42,709 | 0.999985 | 0.517642 |
| 10,000 | 11,871,364 | 32 | 370,980 | 0.999998 | 0.464702 |


It is important to note that Newton's method could have been used for this solution as well, as that would remedy the ill-conditioned Hessian. However, for larger structures or finite element meshes, that Hessian may grow large, and so it may not be desired to calculate or store that Hessian. 

## 6. Assumptions, verification, and limitations

The model makes these assumptions:

- The spar is two-dimensional and statically loaded.
- Every member is straight, linearly elastic, and carries axial force only.
- Joints are perfect pins, so the model excludes joint bending stiffness.
- Displacements and strains are small, so $K$ does not change during deformation.
- Material and cross-sectional properties are ideal and deterministic.
- Geometry, base member stiffness, and load are normalized. The results describe conditioning and solver behavior, not displacement predictions for a specific aircraft.
- This model isolates ill-conditioning rather than structural realism. A higher-fidelity spar study could add beam or shell elements, distributed aerodynamic loads, mass, stress and buckling constraints, three-dimensional geometry, and calibrated material and cross-sectional data.


## 7. Results from Solver

Improving the convergence of a solver is necessary to make the solver practical for use. However, the most important aspect of a solver is whether it actually solves the problem accurately. To ensure accuracy, displacement results for this Warren Truss structure are compared to Ansys MAPDL analysis, as Ansys MAPDL is an independent tool for structural FEA. Below is the result from the conjugate gradient solution, and below that is the result from Ansys. It has a displacement magnitude of 12.01465 mm for this model, compared to a displacement magnitude of 12.0147 mm from Ansys. 
![Deformation from CG](figures/deformed_truss_r10000.png)

<img width="1150" height="875" alt="image" src="https://github.com/user-attachments/assets/0798b383-47d8-4ed0-ae8f-120b2eb905d2" />
Deformation from Ansys



## Reproducibility

Use Python 3.10 or newer. From the project directory, run:

```bash
cd Project2_CodeandMisc
python -m pip install -r requirements.txt
python project2_truss.py
python -m unittest discover -s tests -v
```
For more information about the code or the report, please see [`README.md`](README.md).
The analysis writes figures to `figures/`, a diagnostic table to `results/diagnostics.csv`, and verification values to `results/verification.json`. 

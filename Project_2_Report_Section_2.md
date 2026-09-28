## 2. Mathematical formulation

We seek the horizontal and vertical displacements of the truss nodes under a prescribed load. Although this is a structural equilibrium problem, it can also be formulated as minimizing total potential energy. This formulation allows us to study how differences in member stiffness affect the behavior of optimization algorithms.

### 2.1 Decision variables and parameters

A **decision variable** is a quantity whose value is selected by the optimization problem. The member properties $E$, $A$, and $L$, together with the applied force magnitude, are model parameters in this study; they are not decision variables.

The decision variable is

$$
u=[u_{1x},u_{1y},u_{2x},u_{2y},\ldots]^T,
$$

the vector of unknown nodal displacements. Each of the 14 nodes has two displacement components, giving 28 degrees of freedom. Fixing both root nodes prescribes four of these components as zero, leaving 24 unknown displacements. Therefore, $u\in\mathbb{R}^{24}$, and each candidate vector represents one possible deformed configuration of the truss.

Material properties and member dimensions are prescribed inputs. This problem determines structural displacements; it does not optimize material selection or member sizing.

### 2.2 Truss finite element

Each truss member is modeled as a straight, linearly elastic element that carries axial force only. Its axial stiffness is

$$
k_e=\frac{EA}{L},
$$

where $E$ is Young’s modulus, $A$ is the cross-sectional area, and $L$ is the original member length.

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
u_{ix}\
u_{iy}\
u_{jx}\
u_{jy}
\end{bmatrix}.
$$

Under the small-displacement assumption, the member’s axial extension is the relative displacement of its endpoints projected along its original axis:

$$
\delta_e=c(u_{jx}-u_{ix})+s(u_{jy}-u_{iy}).
$$

Positive $(\delta_e)$ indicates elongation, while negative $(\delta_e)$ indicates shortening. If both endpoints move by the same amount in the same direction, their relative displacement is zero and the member does not stretch.

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

The global stiffness matrix is constructed by adding each member’s stiffness contributions into the rows and columns corresponding to its endpoint displacement coordinates. Members sharing a node contribute to the same nodal equilibrium equations.

The truss has $14$ nodes with two displacement components per node, so the full stiffness matrix is $28\times28$. Both displacement components at each of the two root nodes are fixed at zero. Removing the corresponding four rows and columns applies these boundary conditions and leaves a reduced $24\times24$ stiffness matrix.

In the following sections, $K$ denotes this reduced matrix, $u\in\mathbb{R}^{24}$ contains the unknown free-node displacements, and $f\in\mathbb{R}^{24}$ contains the corresponding applied nodal forces. The total strain energy stored in the supported truss is then

$$
U(u)=\frac12u^TKu,
$$

which provides the elastic-energy term in the optimization formulation.

### 2.3 Minimum-potential-energy problem

The equilibrium displacement minimizes total potential energy:

$$
\min_u \Pi(u)=\frac{1}{2}u^T K u-f^T u,
$$

where (f) is the reduced external force vector. The **potential energy** $\Pi(u)$ contains the strain energy stored in the members, $\frac{1}{2}u^T K u$, minus the work done by the external force, $f^Tu$.

The gradient and Hessian are

$$
\nabla \Pi(u)=Ku-f, \qquad \nabla^2\Pi(u)=K.
$$

The **gradient** gives the slope of the objective with respect to every displacement. The **Hessian** is the matrix of second derivatives; here, the Hessian is exactly the stiffness matrix. Setting the gradient to zero gives

$$
Ku^\star=f.
$$

After the boundary conditions remove rigid-body motion, the computed eigenvalues of $K$ are positive. Therefore, $K$ is **symmetric positive definite**, meaning $x^TKx>0$ for every nonzero vector $x$. The objective is consequently an unconstrained convex quadratic, and $u^\star$ is its unique global minimizer.
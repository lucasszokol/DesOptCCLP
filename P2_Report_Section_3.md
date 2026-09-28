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

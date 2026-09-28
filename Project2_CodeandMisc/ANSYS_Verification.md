# ANSYS Verification Method

This procedure independently reproduces the Python displacement solution for the $r=10{,}000$ truss. The Python analysis automatically writes `results/ansys_model_r10000.inp`, so manual geometry entry is not required.

## 1. Matching model choices

Use a linear static analysis with LINK180 elements. LINK180 is a two-node, axial tension-compression element with translational degrees of freedom $UX$, $UY$, and $UZ$. It does not include member bending, which matches the ideal pin-jointed Python truss.

Use one consistent normalized unit system:

| Quantity | Unit used in ANSYS |
|---|---|
| Coordinate and displacement | mm |
| Force | N |
| Young's modulus | MPa, equal to N/mm$^2$ |
| Area | mm$^2$ |

The export maps one coordinate unit from `truss_config.py` to 1000 mm. This uniform geometry scale does not change any member direction cosine. It uses $E=200{,}000$ MPa and calculates every member area from

$$
A_e=\frac{k_eL_e}{E}.
$$

Therefore,

$$
\frac{EA_e}{L_e}=k_e,
$$

which exactly matches the Python element stiffness. Soft members use $k_e=1$ N/mm, and stiff members use $k_e=10{,}000$ N/mm. Different member lengths require different areas to keep these axial stiffness values exact. The 1000 mm geometry scale also keeps the approximately 12 mm maximum displacement small compared with the 6000 mm span.

## 2. Run the exported MAPDL model

1. Run `python project2_truss.py` to regenerate all outputs.
2. Start ANSYS Mechanical APDL.
3. Set the working directory to the repository `results` folder.
4. Select **File > Read Input From**.
5. Select `ansys_model_r10000.inp`.
6. Wait for the static solution and postprocessing commands to finish.

The input file creates the nodes and LINK180 elements, applies the supports and loads, solves the model, and writes:

- `ansys_nodal_displacements.txt`
- `ansys_reactions.txt`

Python node numbers start at 0, while the exported MAPDL node numbers start at 1. Thus Python node 0 corresponds to ANSYS node 1.

## 3. Boundary conditions and loads

The Python model fixes $UX$ and $UY$ at nodes 0 and 1. The ANSYS model therefore fixes $UX$ and $UY$ at nodes 1 and 2.

LINK180 is a 3D element, so the input file also fixes $UZ=0$ at every node. This removes out-of-plane motion and makes the analysis equivalent to the 2D Python model.

The Python tip loads are:

$$
F_{y,12}=-0.5, \qquad F_{y,13}=-0.5.
$$

The corresponding ANSYS loads are $FY=-0.5$ N at nodes 13 and 14.

## 4. Compare displacements

Open `results/displacements_r10000.csv`. For every node, compare its `u_x` and `u_y` values with the $UX$ and $UY$ columns in `ansys_nodal_displacements.txt`.

Use these tip values as a quick check before comparing every node:

| Python node | ANSYS node | $u_x$ | $u_y$ |
|---:|---:|---:|---:|
| 12 | 13 | $-0.001800$ | $-12.014600$ |
| 13 | 14 | $+0.001800$ | $-12.014650$ |

Under the exported mm-N-MPa convention, these displacement values are in mm.

For each component, calculate relative difference as

$$
\text{relative difference}
=
\frac{|u_{\text{ANSYS}}-u_{\text{Python}}|}
{\max(|u_{\text{Python}}|,10^{-12})}.
$$

The small denominator limit avoids division by zero at supported nodes. Agreement near solver precision is expected because both programs assemble and solve the same linear truss equations. Differences below approximately $10^{-8}$ relative are sufficient for this project.

Also compare total displacement magnitude:

$$
u_{\mathrm{mag}}=\sqrt{u_x^2+u_y^2}.
$$

## 5. Compare reactions

The total applied vertical load is $-1$ N. Therefore, the sum of the ANSYS vertical support reactions should be approximately $+1$ N:

$$
\sum R_y+\sum F_y\approx0.
$$

The horizontal reactions should sum to approximately zero. Check these values in `ansys_reactions.txt` against `full_reaction_vector` in `results/u_r10000.json`. This equilibrium check can reveal an incorrect load, missing support, or node-number mismatch even when a displacement plot looks reasonable.

The expected support reactions are approximately:

| Python node | ANSYS node | $R_x$ | $R_y$ |
|---:|---:|---:|---:|
| 0 | 1 | $+6.0$ N | $+1.0$ N |
| 1 | 2 | $-6.0$ N | $0.0$ N |

Their horizontal sum is zero, and their vertical sum balances the $-1$ N applied load.

## 6. Compare the deformed shape

In MAPDL postprocessing, display the deformed and undeformed shapes together. The overall bending direction and relative node movement should match `figures/deformed_truss_r10000.png`.

The Python figure uses the visual scale stored in `results/u_r10000.json`. This factor adjusts displacement only for plotting. Compare numerical displacement values rather than measuring distances from the image.

## 7. Common mismatch causes

- ANSYS node numbers are one larger than Python node numbers.
- $UZ$ was not fixed at every LINK180 node.
- One or more members use the wrong cross-sectional area.
- Large-deflection analysis was enabled. Keep the verification linear and small-displacement.
- Loads were applied in the wrong direction or to the wrong tip nodes.
- A beam element was used instead of an axial truss element.

## ANSYS references

- [LINK180 element documentation](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_elem/Hlp_E_LINK180.html)
- [ANSYS displacement-constraint command](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/ans_cmd/Hlp_C_D.html)
- [ANSYS Mechanical user-defined displacement results](https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/wb_sim/ds_user_defined_MAPDL.html)

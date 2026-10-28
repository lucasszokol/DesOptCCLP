# Independent validation of the D2Q9 reference solver

Reviewer: Kellen Worthington / Teammate 1. October 26, 2026 (America/Phoenix).

**Decision: FAIL the full reference-adequacy gate on current evidence.** This is a failure to establish an independently validated incompressible reference, not a finding that every operation is incorrect. Core D2Q9 operations pass implementation checks, both stored Re = 10 runs satisfy the programmed stopping rule, and the 2.41% comparison reproduces. However, enforced endpoint volume balance conceals a density-weighted flux mismatch. Local incompressibility, temporal stationarity of density/pressure/forces, curved-boundary accuracy, and external drag accuracy are not established. Treat the fields as provisional.

## 1. Scope and adequacy findings

Source of truth: main at commit **713111f54fe2d821ca19892394a7b7a276676bf2**. Source and stored-output claims refer to that immutable snapshot. Production source, reports, configurations, and outputs were not edited.

PASS means the evidence supports the stated criterion. FAIL includes insufficient evidence; “unverified” does not establish that the physical behavior is wrong. No new acceptance thresholds replace the team's criteria.

| Criterion | Finding | Evidence and limit |
| --- | --- | --- |
| Equilibrium, macroscopic variables, BGK conservation | PASS, implementation | Variable-density first/second moments and actual non-equilibrium collision preserve mass/momentum to roundoff. |
| Streaming and stationary bounce-back indexing | PASS, implementation | One-step tests exercise actual interior streaming and every blocked-link direction. Open-boundary reconstruction takes precedence. |
| Re/viscosity/relaxation scaling in lattice coordinates | PASS, implementation | Re = U_l D_l/nu_l; stored tau = 0.74 fine, 0.62 coarse. |
| Exact physical geometry and isotropic coordinate mapping | FAIL | Exported dx and dy differ by 0.606%; effective halfway walls lie inside declared y = 0, 4.1. |
| Parabolic inlet values on fluid inlet nodes | PASS, implementation | Max nondimensional u error 1.11e-15; v about 2.6e-16. Effective wall/profile geometry remains inconsistent. |
| No-slip accuracy on the true curved cylinder | FAIL, unverified | Correct stationary link reflection on a stair-step approximation does not establish true-circle accuracy. |
| Four consecutive programmed checks | PASS | First qualifying stops are 15,750 fine and 9,750 coarse. |
| Stationary u, v, density, pressure, and drag | FAIL, unverified | Only u change enters stopping; no v, density, pressure, total-mass, or drag histories. |
| Less than 1% endpoint imbalance as defined in code | PASS, enforced | 1.346e-16 fine; 2.694e-16 coarse. This is volume-flux equality, imposed even during large transients. |
| Independent mass/local-continuity verification | FAIL | Reconstructed density-weighted endpoint currents differ; internal section volume-flux departure reaches 1.046% fine, 1.116% coarse. See diagnostic caveats below. |
| Developed outlet and pressure gauge | PASS for approximate final kinematics/mean gauge; FAIL for complete validation | Small final gradients and zero mean outlet pressure; no independent density anchor or reflection test. |
| Coarse/fine comparison implementation | PASS | Reproduced 0.0240985486746362 on the same 5,605 points. |
| Reference discretization accuracy | FAIL, unverified | Two-grid difference is not a continuum error bound; no third grid, lower-Mach run, or predeclared acceptance tolerance. |
| Qualitatively plausible low-Re wake | PASS, limited | Weak reverse center-row velocity and a short wake are compatible with low-Re separation. Full topology is unverified. |
| Drag/wake validated against matched external truth | FAIL, unverified | Re = 10 sources differ in inlet/confinement. Matching-geometry DFG data are Re = 20 with different outflow. |
| Domain-boundary sensitivity | FAIL, unverified | No outlet-length/sensitivity experiment; channel walls are intentional physical confinement. |

The saved reference_adequate flag means only “converged by the u-only rule and endpoint volume imbalance <= 0.01.” It does not implement the complete project gate. Re = 20 and 40 production reference fields are absent at this snapshot; Re = 10 findings cannot certify them.

## 2. Collision, streaming, boundary geometry, and scaling

The rest/axial/diagonal weights are 4/9, 1/9, 1/36. The equilibrium is

\[
f_i^{eq}=w_i\rho[1+3\mathbf c_i\cdot\mathbf u+
(9/2)(\mathbf c_i\cdot\mathbf u)^2-(3/2)|\mathbf u|^2].
\]

Density is sum_i f_i, momentum is sum_i c_i f_i, and BGK relaxation rate is 1/tau. These match standard D2Q9 equations in Zou and He [1]. New tests cover variable rho, nonzero u/v, second moments, and the actual collision on a non-equilibrium distribution, extending the existing unit-density check. The density safeguard substitutes one when rho <= 1e-12; that could obscure nonphysical density if reached. The NPZ omits raw density.

Positive np.roll shifts transport populations along their correct directions. A fluid node facing a solid neighbor returns its outgoing post-collision population to the opposite direction at the same fluid node: stationary halfway link bounce-back. Drag includes only cylinder links. Incoming populations wrapping through x boundaries are subsequently reconstructed; wall-crossing links are reflected. One-step tests verify interior transport and blocked-link indexing, not reflection-free open boundaries.

With N nodes per nominal diameter and U_l = 0.05:

\[
\nu_l=U_lN/Re,\qquad \tau=\tfrac12+3\nu_l,\qquad
u^*=u_l/U_l,\qquad \Delta t^*=U_l/N.
\]

| Re | tau at N = 16 | tau at N = 8 |
| --- | ---: | ---: |
| 10 | 0.74 | 0.62 |
| 20 | 0.62 | 0.56 |
| 40 | 0.56 | 0.53 |

The Re = 10 metadata agree. The 0.515 guard is not a general accuracy/stability guarantee. Inlet peak Mach is 0.1299; saved-field maximum Mach is 0.1764 fine and 0.1792 coarse. Finite-Mach error remains an accuracy question.

**Coordinate issue:** fine nx = 353, ny = 67 gives dx = 0.0625, dy = 0.0621212. Both grids have dy/dx = 0.9939394. Ordinary D2Q9 assumes equal lattice spacings. Stretching exported y coordinates while using one velocity conversion does not give an exactly isotropic physical NS discretization on those coordinates. Both grids share this bias.

**Wall issue:** halfway reflection between solid row 0 and fluid row 1 places the effective lower wall at dy/2; the upper is at H - dy/2. The hydraulic channel is narrowed by dy, approximately 1.515% fine and 3.030% coarse relative to H. The inlet parabola instead vanishes at the solid-node coordinates. Halfway-wall accuracy for consistently located flat walls [1] does not resolve this mismatch. Half-link reflection around the circle approximates a stair-step surface; its position error is of order a grid spacing. Bulk second-order accuracy must not be claimed for the true curved boundary without evidence.

The analytical unit-mean parabola is imposed correctly on inlet nodes. Discrete flux is H(1 - 1/m^2), m = ny - 1: 4.09905877 fine, 4.09623508 coarse, rather than exactly 4.1. This quadrature difference is separate from internal flux variation.

## 3. Mathematical outlet assessment

Let q_in be the prescribed inlet sum of lattice u. Using previous-step penultimate-column velocities a_y, b_y, the outlet sets

\[
s=q_{in}/\sum_y a_y,\qquad u_{b,y}=s a_y,\qquad v_{b,y}=b_y.
\]

For near-zero denominator, rescaling is omitted; equality is not guaranteed in that degenerate branch. Otherwise, defining

\[
A_y=f_0+f_2+f_4+2(f_1+f_5+f_8),
\]

the reconstruction uses rho_b = A_y/(1 + u_b) and fills f_3, f_6, f_7. Directly summing the source formulas gives

\[
\sum_i f_i=\rho_b,\qquad
\sum_i c_{ix}f_i=\rho_bu_b,\qquad
\sum_i c_{iy}f_i=\rho_bv_b.
\]

The signs and transverse terms are algebraically consistent with the velocity boundary formulation [1]. The rescaling enforces **volume** flux, sum u_b = q_in, irrespective of local continuity or density variation. The recorded imbalance uses that same sum; it is not independent evidence.

Even at a fixed point,

\[
\partial_xu|_b\approx(s-1)a_y/\Delta x.
\]

Convergence alone does not imply s = 1. Ratios inferred from the final penultimate fields are 0.99996922 fine, 0.99993134 coarse. These are not exactly the last applied factors because the boundary uses previous-step velocities.

| Final outlet diagnostic | Fine | Coarse |
| --- | ---: | ---: |
| du/dx RMS | 5.4590e-4 | 6.1917e-4 |
| dv/dx RMS | 4.7315e-6 | 7.7417e-7 |
| p mean | 1.82e-14 | -1.57e-14 |
| p RMS | 1.7953e-4 | 3.0482e-4 |
| max abs(p) | 4.2787e-4 | 8.4573e-4 |

Final kinematics are close to developed flow. Temporal stationarity and reflection freedom are not established. Global feedback through s can conceal outlet problems even when its final value is close to one. No fixed density is prescribed during the solve.

Exported p* = (rho - mean_outlet_rho)/(3 U_l^2) shifts a legitimate arbitrary pressure constant. It fixes **mean** outlet pressure, whereas the PINN outlet loss penalizes **pointwise** p = 0, du/dx = dv/dx = 0. The mismatch is small here but real. Gauge subtraction cannot remove density drift or pressure-gradient error. Pressure normalization assumes reference-density unit one, while drag uses actual outlet density; saving that density is necessary to check consistency.

Standard compressible BGK conserves rho u rather than u alone. Equal imposed end volume flux combined with a sustained pressure/density drop can permit mass storage while normalized velocity appears settled. Saved fields support this concern, without establishing its exact population-level accumulation rate.

## 4. Global balance versus local conservation

The read-only checker differentiates only on complete five-point fluid stencils and excludes endpoints/NaN boundaries. Section sums treat solid-node velocity as zero. These are macroscopic finite-difference/quadrature diagnostics, **not exact discrete kinetic link-flux budgets**; near stair-step surfaces they include discretization error.

| Nondimensional diagnostic | Fine | Coarse |
| --- | ---: | ---: |
| max section volume-flux departure from inlet | 1.045617% | 1.116247% |
| divergence RMS, all valid stencils | 0.0103168 | 0.0210864 |
| divergence max abs, all valid stencils | 0.427346 | 0.433971 |
| divergence RMS, away from solids | 0.00383818 | 0.0142783 |
| divergence RMS, wake | 0.00219081 | 0.00428655 |
| divergence RMS, last 2D | 0.000533542 | 0.000582073 |
| absolute lattice density span, reconstructed | 0.0389197 | 0.0412616 |

Away-from-solids means radius > 0.75 and 0.25 < y < 3.85. Wake means 2.75 < x < 8 and 1 < y < 3. Last 2D means x > 20. All intersect the valid stencil. Dimensional divergence scales as U_mean/D. The team specified no divergence threshold; these values do not become an invented formal tolerance. They demonstrate that zero endpoint imbalance does not describe the interior.

**Density-weighted endpoint current can be checked despite the missing absolute density.** Write rho = rho_o + 3 U_l^2 p*, where rho_o is unknown outlet mean density. Equal endpoint velocity sums cancel the unknown constant:

\[
J_{in}-J_{out}
=3U_l^3[\sum_y p^*_{in}u^*_{in}
-\sum_y p^*_{out}u^*_{out}].
\]

With identical nodal weights, this is **+0.08655498 fine** and **+0.04603155 coarse** in lattice density-times-velocity sums. Dividing by inlet lattice volume flux gives **0.02623480** and **0.02792355** in density units. They are not percentages until divided by an actual density. Relative to rho_o Q_in the mismatch is 2.62348%/rho_o and 2.79235%/rho_o. Because rho_o is omitted, a normalized mass-imbalance percentage cannot be certified. Density spans above likewise are absolute, not relative percentages.

This nonzero boundary mass-current proxy rejects the claim “mass consistency proven.” Storage, boundary modeling, compressibility, and quadrature must be distinguished. Decisive next instrumentation:

1. Save rho, rho_o, total fluid mass, and every applied outlet factor.
2. Compare open-boundary incoming/outgoing **population link fluxes** with actual per-step fluid-mass change.
3. Check link budgets in slabs/subdomains and local divergence away from solids.
4. Track rho u and u flux at multiple sections, plus density/pressure/drag after u-only stopping would trigger.
5. Compare outlet perturbation histories under a longer domain or independently anchored outlet.

The added analytical counterexample test has exactly equal endpoint flux but nonzero interior divergence, guarding against the underlying logical mistake.

## 5. Stopping rule and coarse/fine interpretation

Fine passing checks: 15,000, 15,250, 15,500, 15,750, with changes 3.8875e-4, 9.2085e-4, 8.4789e-4, 3.2883e-4. The preceding 14,750 value is 1.2344e-3 and correctly resets the streak. Coarse qualifies at 9,000 through 9,750; 8,750 is 1.0318e-3 and resets the streak. Tests replay all metadata and verify the first qualifying stop.

Only u change is monitored. Both histories contain damped, nonmonotone oscillations. A nominal fine-grid acoustic round trip is approximately 2(352)/(1/sqrt(3)) = 1,219 steps. Four 250-step checks form a 1,000-step block; first-to-fourth sample span is 750. This is insufficient to establish a full-cycle bound on residual oscillations. No specific reflection mode or physical wake unsteadiness is proven by these histories.

The comparison interpolates fine u/v bilinearly to coarse fluid points, excluding nonfinite interpolation stencils:

\[
E_{cf}=\|\mathbf u_c-I_{f\to c}\mathbf u_f\|_2/
\|I_{f\to c}\mathbf u_f\|_2.
\]

The NumPy-only independent implementation reproduces the stored SciPy result to roundoff.

| Comparison | Value |
| --- | ---: |
| full-field relative velocity difference | 2.40985486746% |
| compared points | 5,605 |
| excluded coarse fluid points | 13 of 5,618 |
| wake difference (2.5 < x < 8, 1 < y < 3) | 2.204691% |
| last-2D difference | 1.876278% |
| drag relative difference, denominator fine | 2.909369% |
| raw wake-length relative difference, denominator fine | 33.3333% |

This establishes **resolution sensitivity**, not a 2.41% continuum error bound. Finite-Mach bias, shared coordinate stretching, outlet feedback, geometry and stopping errors can affect both grids. Bulk norms underweight the small near-cylinder region. Fixed lattice speed changes tau across grids and does not reduce Mach error.

Assuming order p and asymptotic behavior could give a fine-error estimate E_cf/(2^p - 1), but neither p nor the asymptotic regime is established. Do not report such an estimate as measured accuracy. A third geometry-consistent grid and reduced lattice speed are needed. No numeric grid-acceptance threshold was stated by the team.

## 6. Drag, wake, and external truth

Drag is 9.05621 fine, 9.31969 coarse, from cylinder-only momentum exchange divided by 0.5 rho_o U_l^2 D_l. Signs and normalization are structurally sensible for a fixed body. Positivity and 2.91% grid sensitivity are implementation/plausibility checks, not external validation. The force is evaluated at collision immediately before the final output field; true stationarity is needed for that offset to be immaterial.

The stored recirculation lengths, 0.1875D fine and 0.125D coarse, are distances to the last negative node, with no zero-crossing interpolation. Both use y = 1.9878788, not the true center y = 2. Interpolating the negative-to-positive crossing on that row gives **0.229738D fine and 0.245250D coarse**, a difference about 6.75% relative to fine. Raw 33% difference is strongly affected by grid quantization. Fine minimum center-row wake u is -0.0079628: this is a weak short bubble, sensitive to geometry and sampling. Interpolation does not remove row-offset error.

| Primary comparison | Published quantity | Interpretation |
| --- | --- | --- |
| Perumal et al. (2012), circular-cylinder validation, Table 1 [2] | Re = 10 C_D = 3.21; H/D = 8 configuration | Weaker confinement than our H/D = 4.1 parabolic channel; not a matched acceptance target. |
| Yousefifard et al. (2013), section 4/Table 1 [3] | Own Re = 10 wake lengths 0.260D, 0.262D; uniform inlet, H/D = 10, long domain | A short attached bubble of order 0.2D is plausible. Different confinement/profile prevent quantitative validation of our 0.230D. |
| Official DFG 2D-1 benchmark [4] | Same nondimensional geometry, Re = 20: C_D = 5.57953523384, C_L = 0.010618948146 | Strong future solver cross-check, with do-nothing traction outlet rather than our rescaled velocity condition. Not a Re = 10 benchmark. |

No retrieved source supplies matched Re = 10 drag/wake truth for the exact current boundaries. C_D near nine remains **unvalidated**; comparison with weakly confined/unconfined drag near three alone does not disprove it. The local inlet speed at y = 2 is 1.4991 times the mean; using that normalization changes C_D by a factor about 2.247 and also changes the associated Re. This illustrates why conventions cannot be mixed, not a correction that makes different cases equivalent.

The cylinder is 0.05D below channel midheight, so exact lift zero/mirror symmetry is not required. Cylinder front is 1.5D from inlet and rear is 19.5D from outlet. These are intended physical boundaries. Extending the outlet tests truncation; widening the channel instead changes confinement. Moving the inlet also creates a different-domain experiment and must be labelled. A streamline/topology check, lift, pressure-force comparison, and stationary drag/wake histories remain outstanding.

## 7. Ranked risks and smallest corrective experiments

Proposals below are for coordination with the production solver owner; **none was applied to production**.

| Rank | Risk | Smallest useful experiment/proposed patch |
| --- | --- | --- |
| 1 | u stationarity can hide density/mass drift; reconstructed mass currents differ | Instrument one existing-grid Re = 10 rerun with rho_o, fluid mass, density/pressure/drag histories, exact boundary link fluxes, outlet factor. Continue several acoustic round trips past the existing stopping trigger. Establish the actual budget before changing the outlet. |
| 2 | Finite-Mach bias and unanchored density | At N = 16 rerun U_l = 0.025, recompute nu/tau, extend steps to comparable nondimensional time; compare velocity/pressure/drag, density span and storage. If needed, owner tests a fixed-density Zou-He pressure outlet in isolation, explicitly acknowledging the boundary-model change. |
| 3 | Effective wall/circle and coordinate stretching differ from the PINN geometry | First run cylinder-free pressure-driven Poiseuille flow with current wall convention and fit hydraulic height/viscosity. Then use consistent isotropic coordinates and curved geometry. Relabelling y alone is insufficient. |
| 4 | Two grids and quantized wake extraction do not establish accuracy | Add N = 32 after resolving geometry conventions; compare bulk, near-circle, wake norms and drag; interpolate crossings at y = 2. |
| 5 | No matched external force validation | Re = 20 DFG comparison with reconciled outlet, or an independently converged FEM/FVM solution of the exact current Re = 10 model. Include lift and front/rear pressure difference. |
| 6 | Possible outlet feedback/reflection | Extend length 22D to 32D at the same local spacing and inlet/cylinder positions; compare shared-domain fields, force and outlet histories. |
| 7 | Cached fields can be returned for changed config | Owner adds source/geometry/config fingerprint verification, or use unique experiment directories. Never overwrite production output for these checks. |
| 8 | Adequacy flag omits required validation; rho_o missing | Owner separates convergence/balance/grid/validation flags and saves raw rho/rho_o plus provenance. Document the existing flag's narrow meaning meanwhile. |

For this one-week study, rank 1 and a reduced-speed comparison should precede treating these fields as external truth. Reference uncertainty affects supervised capacity control and every field-error comparison. Re = 10 improvements still would not validate the primary Re = 40 target.

## 8. Exact files, commands, tests, sources

### Inspected files

All paths relative to repository root:

- Project 3/project3_pinn/lbm.py, blob **6b6722badfebf6d17d1e6ed49ab4e25b4fcc851b**: equilibrium/macroscopic (21-34), grid/scaling (49-75), collision/stream/bounce-back (83-97), inlet (99-123), outlet (125-161), stopping (164-182), pressure/drag/wake/metadata (185-232), refinement (240 onward).
- Project 3/project3_pinn/config.py, geometry.py, __init__.py.
- Project 3/project3_pinn/pinn.py (especially outlet loss, 125-134), analysis.py, cli.py.
- Project 3/tests/test_project3_pinn.py; Project 3/requirements-project3.txt; Project 3/PROJECT3_README.md; Project 3/Project_3_Report.md.
- Project 3/project3_results/experiment_config.json.
- Project 3/project3_results/reference/cylinder_re10.json and .npz.
- Project 3/project3_results/grid_check/coarse/reference/cylinder_re10.json and .npz.
- Project 3/project3_results/analysis/lbm_grid_refinement.json.

NPZ bytes: 502,634 fine; 127,033 coarse. SHA-256:

- Fine: 255cd0b519f3c92b2e759e32c3a9d462df9c2408ae77f0c296e790d7b97939a4.
- Coarse: 64d8d16e6b63f554a31262f2ad9d5f65323f7307ac3fad9a67fcc1312e4dcd9e.

### Changed files

- Project 3/reviews/reference_solver_validation.md.
- Project 3/reviews/check_reference_fields.py: read-only NumPy diagnostics, deliberately specific to this saved D = 1 geometry and U_l = 0.05 experiment.
- Project 3/tests/test_reference_solver_validation.py: six independent tests.

No environments, caches, temporary experiments, production results, or production-source patches are committed.

### Execution and limitations

Local clone attempts failed: first workspace directory access, then GitHub DNS from a writable temporary directory. The connected GitHub plugin read the immutable tree and file content, including NPZs via base64. This is a **materialized snapshot audit**, not a successful local clone/pull. Branch: **project3/kellen-reference-validation**, based on the reviewed main SHA. Repository writes and PR use the connector.

Initial audit runtime: Python 3.12.14, NumPy 2.3.5. SciPy and PyTorch were absent. SciPy interpolation was independently reproduced using NumPy, not mocked. No full production reference was regenerated; one- and two-step tests used unique temporary directories.

Commands, from Project 3:

~~~powershell
python -m unittest tests.test_project3_pinn -v
python -m unittest tests.test_reference_solver_validation -v
python reviews/check_reference_fields.py
~~~

Actual executable:

C:\Users\kelle\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

Actual working directory:

C:\Users\kelle\AppData\Local\Temp\DesOptCCLP-review\Project 3

Each command used that executable via PowerShell &. Initial complete-suite invocation failed on two sandbox temporary-directory permissions. Setting process-local TEMP and TMP to the permitted C:\Users\kelle\AppData\Local\Temp resolved them without source edits.

- Required suite on rerun: 10 discovered, **8 passed, 2 skipped**, no failures/errors.
- Independent suite: **6 passed**, no failures/errors/skips.
- Field checker: completed; grid comparison reproduces to roundoff.

The initially skipped tests were PyTorch manufactured-field autodiff and all-15-gradient-cosines checks.

### Follow-up verification with PyTorch installed

The user installed an isolated environment at C:\Users\kelle\AppData\Local\Temp\DesOptCCLP-review\.venv. Verified imports: PyTorch 2.7.0+cpu, NumPy 2.5.4, SciPy 1.18.1, Python 3.12.14.

Using that environment's Scripts\python.exe, from the same Project 3 working directory, with the same permitted process-local TEMP/TMP:

~~~powershell
python -m unittest tests.test_project3_pinn tests.test_reference_solver_validation -v
~~~

**All 16 tests passed, with no skips or failures**, including both previously skipped PyTorch tests. These were CPU tests; CUDA/GPU execution was not tested. No production-source changes were needed.

Also executed the original SciPy-based grid_refinement_check(ExperimentConfig with reynolds_numbers=(10,), reynolds=10) using the existing fine/coarse fields, without forcing regeneration. It returned **0.024098548674635872 on 5,605 points**, agreeing with the stored result and the independent NumPy implementation. Only the temporary snapshot's analysis JSON was rewritten; no production result changes were committed.

This follow-up resolves the missing-test-dependency limitation. It does not resolve the independent conservation, geometry, or external-validation concerns above.

### Primary sources used

[1] Q. Zou and X. He, *On pressure and velocity flow boundary conditions and bounceback for the lattice Boltzmann BGK model*, arXiv:comp-gas/9611001; related Physics of Fluids 9 (1997), 1591-1598, DOI 10.1063/1.869307. Equations (1)-(5), boundary and halfway-wall discussion. [Primary preprint](https://arxiv.org/pdf/comp-gas/9611001). This distinguishes standard compressible BGK from an improved incompressible model; the repository uses standard density-weighted equilibrium.

[2] D. Arumuga Perumal, G. V. S. Kumar, A. K. Dass, *Numerical Simulation of Viscous Flow over a Square Cylinder Using Lattice Boltzmann Method*, (2012), 630801, DOI 10.5402/2012/630801. **Circular-cylinder validation**, section 2.1/Table 1, supplies its Re = 10 drag. Square-cylinder results are not treated as circular-cylinder truth. [Publisher full text](https://onlinelibrary.wiley.com/doi/10.5402/2012/630801).

[3] M. Yousefifard, P. Ghadimi, R. Zamanian, *Unstructured Grid Solutions for Incompressible Laminar Flow over a Circular Cylinder Using a Particular Finite Volume-Finite Element Method*, Journal of Engineering (2013), 795237, DOI 10.1155/2013/795237. Sections 4-5/Table 1 provide geometry, inlet, and own Re = 10 wake results. [Publisher full text](https://onlinelibrary.wiley.com/doi/10.1155/2013/795237). Its cited Ding results are not represented as separately read primary evidence.

[4] TU Dortmund/FEATFLOW, *DFG flow around cylinder benchmark 2D-1, laminar case (Re = 20)*. [Official geometry, conditions, normalization and reference values](https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/cfdbenchmarking/flow/dfg_benchmark1_re20.html). A future matched-geometry check, not published Re = 10 truth.

Accessed October 26, 2026 local time. Mismatched 3D finite-cylinder studies and secondary summaries surfaced in searches but were not used as validation evidence.

---
layout: default
title: PDE-Constrained Heat-Sink Optimization
---

# PDE-Constrained Heat-Sink Optimization

A plate-fin heat sink spreads heat from a power chip into ambient air. We seek the least aluminum mass that meets chip-interface temperature limits under both nominal and overload conditions. The limits are engineering targets, not a component qualification.

<div class="gate"><strong>Data status:</strong> <span id="data-status">loading</span>. All displayed results and geometry come from <code>assets/results.json</code>. Preliminary output is not an optimized result.</div>

## Summary and interactive comparison

The views share the same camera orientation and scale. Drag to orbit and scroll to zoom; hover or click a fin to inspect it. During history playback, the raw-density geometry preview is gray because historical temperature fields and filtered densities are not stored; reload to return to the final field. Geometry is extruded at its modeled dimensions, without visual exaggeration. Candidate fins are shown or hidden according to the configured threshold applied to raw density; the thermal model uses filtered density, so the thresholded view is a representation of topology rather than an exact picture of intermediate material. The field shown is the nominal-load temperature: the base faces approximate bilinear quadrilateral interpolation and each fin uses linear interpolation between its nodal temperatures. It is uniform through the extrusion depth, as assumed by the reduced model. The black outlined markers identify fin segments containing a nodal temperature over the nominal limit; the actual constraint applies to the aggregate of chip-interface temperatures, not these markers.

<div class="controls"><button id="play-history">Play optimization history</button><span id="history-status" aria-live="polite"></span></div>
<div class="legend"><span>Nominal field temperature (K)</span><span id="scale-min">—</span><span class="colorbar"></span><span id="scale-max">—</span></div>
<div class="viewer-labels"><strong>Initial</strong><strong>Optimized</strong></div>
<div id="viewer"><div id="tooltip" role="status"></div><p id="viewer-status">Loading interactive viewer…</p></div>
<div id="metrics" class="metrics"></div>
<script type="module" src="assets/viewer.js"></script>

## Structure and formulation

Each candidate fin has a height $H_i$ and a raw density $\rho_i$; the filtered density is $\bar\rho_i$. The configured geometry, loads, bounds and material assumptions are recorded in the reproducibility input. All design quantities shown below are loaded from the generated results file.

$$m=\rho_{Al}\left(V_b+d t_f\sum_i\bar\rho_iH_i\right),\qquad g_c=\frac{\mathrm{KS}(T_{\mathrm{chip},c})}{T_{\mathrm{lim},c}}-1\le 0.$$

The KS function is a smooth upper bound for the chip-interface nodal maximum. Both load cases must satisfy their respective constraint. The engineering limits are project assumptions. Density filtering and SIMP interpolation regularize the topology problem; they also mean intermediate densities are a computational representation, not automatically manufacturable fins.

<div id="geometry-summary" class="data-panel">Loading model dimensions…</div>

## Analysis and assumptions

The steady conduction equation is $-\nabla\cdot(k\nabla T)=0$ in the solid with a prescribed chip heat input and convection and radiation on exposed surfaces. The base is meshed with bilinear quadrilaterals, while each fin is a coupled one-dimensional line mesh. The nonlinear surface flux is

$$q_s=h(T)(T-T_\infty)+\epsilon\sigma(T^4-T_\infty^4),\qquad h\propto |T-T_\infty|^{1/4}.$$

The finite-element residual is solved with Newton's method and a consistent tangent. Assumptions include constant conductivity, a uniform extrusion, no thermal contact resistance, and an adiabatic underside away from the chip. Natural convection is an approximate correlation and emissivity is an assumed surface property. The fin model does not resolve temperature gradients across the thickness or extrusion depth.

## Verification

The verification ladder compares independent student-derived benchmarks with the solver and checks convergence, balance, invariance, units, and the nonlinear tangent. The table below only reports evidence contained in this snapshot; missing evidence must not be interpreted as a pass.

<div id="verification-summary" class="data-panel">Loading verification evidence…</div>

## Adjoint derivation and sensitivity checks

For a response $f(T,x)$ subject to $R(T,x)=0$, differentiation gives $R_T\,dT/dx+R_x=0$ and $df/dx=f_x+f_T\,dT/dx$. Choosing $R_T^T\lambda=-f_T^T$ eliminates the state derivative:

$$\frac{df}{dx}=f_x+\lambda^T R_x.$$

The mass objective has an explicit design derivative. Each temperature constraint uses the derivative of its KS aggregate and one adjoint solve with the converged tangent; the same derivation applies to both load cases. Derivatives propagate through the density filter. The checks compare adjoints with finite differences and examine Taylor remainders before roundoff dominates.

<div id="gradient-summary" class="data-panel">Loading sensitivity evidence…</div>
<canvas id="taylor-plot" class="report-plot" width="900" height="360" aria-label="Taylor-test error plot"></canvas>

## Optimization

The planned comparison uses scaled SLSQP stages for fixed and variable topology, followed by thresholding, height re-optimization, and a trust-constr polish. Convergence, starting-point dependence, active constraints, multipliers, and their engineering interpretation require the completed campaign; they are not inferred from the starting design.

<div id="kkt-summary" class="data-panel">Loading optimizer evidence…</div>
<canvas id="history-plot" class="report-plot" width="900" height="360" aria-label="Optimization convergence plot"></canvas>

## Nonlinear comparison

The linear model uses constant convection without radiation; the nonlinear model uses temperature-dependent convection and radiation. The results table compares the resulting optimized designs when both are supplied. No change in mass or geometry is claimed until both runs are available and verified.

## Results

The panels and table show mass and every available load-case constraint. PASS and FAIL describe the exact reported inequality; they are not a certification of the model or optimizer convergence.

<div id="results-table"></div>

## Bonus: fully nonlinear analysis

The nonlinear residual is solved at equilibrium using Newton's method. Its converged tangent also enters the implicit adjoint. The nonlinear benchmark and final comparison are needed to establish the bonus evidence.

## Bonus: topology

Filtered fin densities and a positive density floor regularize the ground structure. SIMP continuation encourages discrete designs, after which the thresholded topology is to be re-optimized and compared with fixed topology. A gray design is not presented as a final manufactured layout.

## Reproducibility

Install `Project4/requirements-project4.txt` and run from the repository root:

```text
python -m Project4.heatsink.run_all --config Project4/config.yaml
```

The run requires the human approval and independently authored benchmark files and stops when verification fails. The serialized results file is the source for the report and viewer.

## Limitations

This reduced thermal model omits contact resistance, detailed airflow between fins, and manufacturing effects. The natural-convection correlation and emissivity require validation for the actual orientation and surface finish. A local optimum does not establish global optimality. Results should not be used as a component rating without further validation.

## AI-use statement — human wording review pending

A coding agent assisted with the model, adjoint, optimization interface, report and viewer. Students supplied the independent benchmark answers and must review the equations and the final AI-use statement. The documented feasibility check caught an infeasible early load specification before optimization. The team should verify the scope of its own checks and finalize this statement before submission.

## References

1. Hydro, [Alloy 6061 data sheet](https://www.hydro.com/globalassets/01-products--services/extruded-profiles/americas/ena-resources/alloy-data-sheets/hydro_2019_data_sheet_6061.pdf).
2. NIST, [Fundamental Physical Constants](https://physics.nist.gov/cuu/Constants/).
3. Sandia, [natural-convection correlations](https://www.sandia.gov/files/sierra/Aria_Users_5_24/simulation_setup/advanced_feat/correlation_heat_transfer_coeff_reference.html).
4. [Course Project 4 brief](https://designinformaticslab.github.io/DesignOptimization2025/project4.html).

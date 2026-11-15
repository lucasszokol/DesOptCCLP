---
layout: default
title: PDE-Constrained Heat-Sink Optimization
---

# PDE-Constrained Heat-Sink Optimization

**Team Optimus Prime:** Charles Green, Christian Miranda, Kellen Worthington, Lucas Somoshegyi-Szokol, and Polina Kondratiuk

<div class="gate"><strong>Data status:</strong> <span id="data-status">loading</span>. Numerical results are loaded from <code>assets/results.json</code>.</div>

## Summary and live 3D comparison

We minimize the mass of a passively cooled 6061-T6 aluminum heat sink subject to nominal and overload chip-temperature limits. The initial and optimized ground-structure designs are shown with one linked camera. Geometry is drawn at true scale; no fin thickening is used. Colors show the nominal case, interpolating base Q4 and fin linear nodal temperatures; dark outlines indicate a part with at least one node over the nominal limit. During the history animation geometry changes while colors remain the final-state field, since fields were not saved at each iteration.

<div class="controls"><button id="play-history">Play/pause optimization history</button><span>Temperature</span><div class="colorbar" style="width:220px"></div><span>low → limit</span></div>
<div id="viewer"><div class="viewer-labels"><strong>Initial</strong><strong>Optimized</strong></div><div id="tooltip"></div></div>
<div id="metrics" class="metrics"></div>
<script type="module" src="assets/viewer.js"></script>

## Structure and formulation

The design domain is a 60 mm × 50 mm extruded heat sink with a 5 mm base and twenty candidate plate fins. The forty primary variables are fin heights $H_i$ and filtered topology densities $\rho_i$. The objective is

$$m=\rho_{Al}\left(V_b+d t_f\sum_i \bar\rho_iH_i\right).$$

Two PDE response constraints limit a KS aggregate of the chip-interface temperature: 358.15 K at 50 W and 298.15 K ambient, and 373.15 K at 60 W and 308.15 K ambient. Heights are bounded from 10–55 mm and densities from 0.001–1. A bounding analysis rejected the original 100/125 W draft because even the maximum-material design was infeasible; this is the first documented bug caught by verification.

For load case $s$, the explicit scaled constraint is $g_s=\mathrm{KS}_{\beta}(T_{chip,s})/T_{limit,s}-1\le0$, where

$$\mathrm{KS}_{\beta}(T)=T_{\max}+\beta^{-1}\log\!\sum_j\exp[\beta(T_j-T_{\max})].$$

The limits are project engineering targets, not a specific chip datasheet. The mass expression counts a fixed base plus filtered fin volumes; the ground-structure variables are raw densities, filtered before use in the physics and mass. Constants, bounds, mesh and loads are recorded in the repository's configuration.

## Analysis model

The custom solver uses bilinear quadrilateral conduction elements in the base and coupled linear one-dimensional fin elements. The extruded depth is included in conduction, mass, heat input, and surface loss. The nonlinear boundary residual is

$$q_s=h(T)(T-T_\infty)+\epsilon\sigma(T^4-T_\infty^4),\qquad h\propto|T-T_\infty|^{1/4}.$$

Newton's method uses the consistent analytic tangent and backtracking. The model currently has 365 thermal degrees of freedom. Assumptions include an isothermal material conductivity, no contact resistance, an adiabatic underside outside the chip, and a reduced-order 1D representation of each plate fin.

The base solves $-\nabla\cdot(k\nabla T)=0$ in its cross-section. A prescribed heat flux is applied over the centered chip footprint; exposed surfaces lose heat through the boundary law above, and the remainder of the underside is insulated. Each fin carries axial conduction coupled to its base node and loses heat from its sides and tip. The model does not resolve air flow or mutual fin shielding, so extrapolating to a manufactured design requires external validation.

## Verification

The team independently supplied benchmark values before the agent checked the solver. The ladder covers exact conduction and fin solutions, mesh convergence, energy balance, reflection and unit invariance, a nonlinear benchmark, and gradient checks.

<div id="verification-summary" class="data-panel">Verification evidence awaits the student worksheet.</div>

## Sensitivities

For residual $R(T,x)=0$ and response $f(T,x)$, each discrete adjoint solves

$$R_T^T\lambda=-f_T^T,\qquad \frac{df}{dx}=f_x+\lambda^TR_x.$$

This follows by differentiating $R(T(x),x)=0$: $R_TT_x+R_x=0$. Multiplying by $\lambda^T$ eliminates $T_x$ from the total derivative. For each scaled temperature constraint $f_T$ is the KS softmax weight vector divided by its temperature limit and $f_x=0$ at fixed state. Mass is independent of the thermal state, so its gradient is computed directly. The same adjoint relation applies to the converged nonlinear tangent.

The implementation includes analytic $R_x$ for every height and raw density, including density-filter propagation, SIMP conduction, changing fin length, and density-scaled surface loss. The table compares adjoint and central-difference directions for both load cases and both variable families.

<div id="sensitivity-summary"></div>

<canvas id="taylor-plot" class="report-plot" width="900" height="360" aria-label="Taylor-test error plot"></canvas>

## Optimization

The staged campaign uses SLSQP for the linear fixed-topology, nonlinear fixed-topology, and SIMP-continuation studies, followed by a `trust-constr` KKT polish. Heights are scaled by the maximum height and mass by the starting mass. The overload constraint governs the reported nonlinear solution. Every iteration stores the design, mass, and constraint values for the animation.

<div id="kkt-summary"></div>

<canvas id="history-plot" class="report-plot" width="900" height="360" aria-label="Optimization convergence plot"></canvas>

## Nonlinear component — bonus +5

The N2 state includes temperature-dependent natural convection and $T^4$ radiation, is solved by Newton's method, differentiated at the converged state, and checked against the independently solved nonlinear benchmark. The linear and nonlinear fixed-topology optima are listed in the results table. The linear reference uses the approved constant $h=15\,\mathrm{W/(m^2K)}$ without radiation, so the difference reflects both the boundary-law change and the chosen reference coefficient; it should not be interpreted as an isolated radiation effect.

## Ground-structure topology — bonus +5

Candidate fins may vanish through filtered density variables. A density floor prevents singular conduction matrices, SIMP continuation discourages gray fins, and a one-dimensional filter suppresses alternating artifacts. Filtering makes an isolated thresholded raw density differ from the physical density, so mixed topologies need further validation before they can be treated as removed fins.

We compare the continuation solution with two additional asymmetric $p=3$ starts, one with an edge fin and one with an interior fin initialized at the density floor. The additional starts do not repeat the full continuation schedule. Successful feasible candidates compete on mass before thresholding and height re-optimization.

<div id="topology-starts"></div>

## Design under uncertainty — bonus +5

The scenario study perturbs each load case to paired low and high power and ambient conditions. These are illustrative bounded scenarios, not a measured probability distribution or a reliability guarantee. Each scenario is constrained separately and its adjoint gradient is checked against central differences.

<div id="uncertainty-summary">Uncertainty study awaits a verified run.</div>

## Results

The table compares mass and both temperature constraints. PASS allows the configured scaled feasibility tolerance of $10^{-4}$.

<div id="results-table"></div>

## Reproducibility

From the repository root, install `Project4/requirements-project4.txt`, complete the human input files, then run:

```text
python -m Project4.heatsink.run_all --config Project4/config.yaml
```

## Limitations and AI-use statement

The solver, adjoint, optimizer interface, serialization, and viewer were drafted with a coding agent. The students independently supplied the benchmark truth and checked the benchmark derivations; the team must review this statement before submission. A feasibility bound caught a substantive specification bug: the original 100/125 W cases admitted no feasible design, so the documented study cases were corrected to 50/60 W before optimization. Reduced-order fins and empirical natural convection limit predictive fidelity; the results are a design study, not certification data.

## References

1. [Hydro, “Alloy 6061” data sheet](https://www.hydro.com/globalassets/01-products--services/extruded-profiles/americas/ena-resources/alloy-data-sheets/hydro_2019_data_sheet_6061.pdf), thermal conductivity and density.
2. [NIST, Fundamental Physical Constants](https://physics.nist.gov/cuu/Constants/), Stefan–Boltzmann constant.
3. [Sandia SIERRA/Aria documentation](https://www.sandia.gov/files/sierra/Aria_Users_5_24/simulation_setup/advanced_feat/correlation_heat_transfer_coeff_reference.html), Churchill–Chu natural-convection correlation.
4. Course [Project 4 brief](https://designinformaticslab.github.io/DesignOptimization2025/project4.html).

# Frozen Engineering Specification

Status: **team approved**, including the DEC-002 amendment on 2026-11-11

## Engineering problem

Design an extruded, passively cooled plate-fin heat sink for a power chip. The
solid is 6061-T6 aluminum. The design minimizes aluminum mass while satisfying
two chip-interface temperature requirements.

| Item | Value |
|---|---:|
| Base width | 60 mm |
| Extrusion depth | 50 mm |
| Base thickness | 5 mm |
| Chip-heating width | 20 mm, centered on the lower base face |
| Candidate fins | 20 equally spaced ground-structure locations |
| Fin thickness | 1.0 mm in the primary study |
| Fin-height bounds | 10–55 mm |
| Topology-density bounds | 0.001–1.0 |
| Nominal case | 50 W, ambient 25 °C, aggregated chip temperature ≤ 85 °C |
| Overload case | 60 W, ambient 35 °C, aggregated chip temperature ≤ 100 °C |

The 40 primary design variables are the 20 fin heights and 20 raw fin-density
variables. A density filter acts only along the ordered fin locations. The
fixed-topology comparison sets every density to one. The topology study uses a
SIMP conduction interpolation, penalization continuation, density filtering,
binary thresholding, and a final height re-optimization.

The objective is

$$
m(\mathbf{x})=\rho_{Al}\left(V_{base}+d\,t_f
\sum_{i=1}^{20}\bar\rho_i H_i\right).
$$

Each temperature constraint uses a smooth KS aggregate of the chip-interface
nodal temperatures. All optimization constraints are scaled to order one.

## Governing model

The base uses bilinear quadrilateral conduction elements in a two-dimensional
cross-section. Each candidate fin uses one-dimensional conduction elements
coupled to a top-face base node. The extrusion depth supplies the out-of-plane
area and exposed surface.

The linear comparison uses constant convection with
$h=15\ \mathrm{W/(m^2\,K)}$ and omits radiation. The N2
model uses

$$
q_s(T)=h(T)(T-T_\infty)+\epsilon\sigma(T^4-T_\infty^4),
\qquad h(T)\propto |T-T_\infty|^{1/4},
$$

solved with Newton's method, an analytic tangent, backtracking line search, and
load continuation if needed. The converged tangent is also used in the
discrete adjoint.

## Sourced constants and assumptions

- 6061-T6 conductivity: 167 W/(m·K); density: 0.098 lb/in³
  (approximately 2710 kg/m³). Source: Hydro, *Alloy 6061* data sheet,
  <https://www.hydro.com/globalassets/01-products--services/extruded-profiles/americas/ena-resources/alloy-data-sheets/hydro_2019_data_sheet_6061.pdf>.
- Stefan–Boltzmann constant: 5.670374419×10⁻⁸ W/(m²·K⁴), using the current SI
  exact-constant formulation. Source: NIST Fundamental Physical Constants,
  <https://physics.nist.gov/cuu/Constants/>.
- Natural-convection form: the quarter-power dependence is the laminar
  reduction of the Churchill–Chu vertical-plate correlation. A government
  reference implementation is documented by Sandia,
  <https://www.sandia.gov/files/sierra/Aria_Users_5_24/simulation_setup/advanced_feat/correlation_heat_transfer_coeff_reference.html>.
- Surface emissivity is initially 0.80 for a black-anodized finish. This is a
  modeling assumption and will be labeled as such unless the team supplies a
  specific finish data sheet.
- The two temperature limits are project engineering targets, not claims from
  a component data sheet. A named chip/module may replace them only if its
  thermal interface and datasheet limit are modeled consistently.

## Feasibility correction caught before optimization

The first draft used 100 W nominal and 125 W overload. A bounding analysis of
the all-solid design at the maximum 50 mm fin height produced KS temperatures
of 393.74 K and 417.87 K, so no admissible design could satisfy the 358.15 K
and 373.15 K limits. The power cases were corrected to 50 W and 60 W. The same
maximum-material bound then gives 356.35 K and 372.59 K, proving that the
design domain contains a feasible point while the 30 mm starting design still
fails both constraints. This check prevents an optimizer from being blamed for
an infeasible engineering specification.

## DEC-002 feasibility amendment

The team approved an increase of the fin-height upper bound from 50 mm to
55 mm after a bounding check showed that no thresholded topology with a
vanished fin could satisfy both load cases under the original cap. The team
also approved $h=15\ \mathrm{W/(m^2\,K)}$ for the linear reference comparison;
the nonlinear N2 physics remains unchanged. Design under uncertainty is the
backup bonus path if the topology result receives limited credit.

## Approval statement

The original specification and DEC-002 amendment are recorded in
`approvals.yaml`. Kellen Worthington is confirmed as a Project 4 author.

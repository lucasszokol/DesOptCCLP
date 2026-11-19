# DEC-003 — Chip footprint and mesh-consistent temperature evaluation

Status: **team approved on 2026-11-19**. The team confirmed the 15 fixed
sampling points and 0.5 K reserve for the revised final design.

The approved loads, ambient conditions, material, geometry bounds, and chip
temperature limits are unchanged. An audit found that the former midpoint-edge
selection applied power over 21 mm instead of the specified 20 mm, while
the KS sum used a mesh-dependent number of chip nodes. On the prior published
design, refining the base mesh changed overload KS from 373.150 K to 376.253 K,
although the physical peak moved by roughly 0.32 K.

The correction integrates heat-flux shape functions over the exact
20 mm footprint, including partial elements. KS uses 15 fixed physical positions
across that footprint, including its endpoints and the original 13 interior
coarse-mesh nodes. FE interpolation evaluates those points at every mesh.
The original KS parameter remains unchanged. The maximum of the full
piecewise-linear chip interface is reported separately.

The optimizer additionally holds the fixed-sample KS temperature 0.5 K below
each approved engineering limit. This numerical reserve accounts for observed
base-mesh changes; it is not a component limit, a probabilistic safety factor,
or a proof of convergence at infinite mesh resolution. The final design and
uncertainty design are reanalysed at 40×4, 160×16, 320×32, and 400×40 base
elements. The original limits must pass on every mesh and the KS change on
the last refinement must be no more than 0.1 K.

Sparse assembly and solves do not change the physical problem. The trust-constr
joint-design Hessian is corrected to include height/density cross terms; the
previously published fixed-topology polish did not use those mixed terms.

This amendment changes the numerical aggregate and adds a design reserve.
The team approved those settings for the revised final design. Human benchmark
truth is unchanged; final deployment and submission checks remain necessary.

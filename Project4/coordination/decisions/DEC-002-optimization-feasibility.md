# DEC-002 — Optimization feasibility and bonus strategy

Status: **approved 2026-11-11**

Date: 2026-11-11

## Evidence

The approved design domain uses 20 candidate fins with a 50 mm height cap.
The all-solid, maximum-height nonlinear design is only narrowly feasible. A
direct bounding check that removes the least important edge fin while leaving
all other fins at 50 mm gives scaled nominal and overload constraints of
`+0.00040275` and `+0.00434207`. Therefore no thresholded design with even one
vanished fin can be feasible inside the approved domain.

For the edge-fin-removed design:

- the maximum feasible nominal power at 50 mm is `49.8288 W`;
- the maximum feasible overload power at 50 mm is `57.9586 W`;
- at the approved 50/60 W loads, the minimum common fin-height cap is
  `52.8072 mm`.

A clean 55 mm cap makes the one-edge-fin-removed maximum-height design
feasible, with scaled constraints `-0.00665892` and `-0.00308638`. This change
preserves the material, footprint, fin count, loads, and temperature limits.

The linear comparison is separately infeasible with the current constant
`h = 10 W/(m² K)`: even the all-solid maximum-height design violates both
constraints. At the original 50 mm cap, feasibility requires at least
`h = 12.5593 W/(m² K)`. A documented comparison value of
`15 W/(m² K)` is proposed; it changes only the linear reference model, not the
fully nonlinear N2 design constraints.

## Optimizer findings

Adding `keep_feasible=True` to SciPy bounds prevents the final KKT stage from
probing non-positive element lengths, but the current campaign still fails
acceptance:

- the linear fixed-topology run exits unsuccessfully and infeasibly;
- the final KKT run exits unsuccessfully with scaled violation `3.9826e-4`,
  above the configured `1e-4` tolerance;
- SIMP continuation returns every density at exactly one.

Even with a runtime-only 55 mm bound and asymmetric edge-fin-removed starts,
the continuous relaxation returns to the lower-mass all-solid sizing design.
This is a defensible engineering finding—the current independent-fin heat-loss
model rewards retaining many shorter fins—but it weakens the topology-bonus
story and must be reported honestly.

## Proposed decision

Approve both of the following specification clarifications:

1. Increase the fin-height upper bound from 50 mm to **55 mm**.
2. Set the linear comparison coefficient to **15 W/(m² K)**, while retaining
   the approved N2 convection/radiation model for the final design.

Agent 3 must then run multiple asymmetric starts, enforce optimizer success and
feasibility before serialization, and compare the best variable-topology result
with the fixed-topology optimum even if the optimum remains all-solid.

To secure at least 10 bonus points if the all-solid topology result receives
limited credit, add the **design-under-uncertainty** bonus: several documented
power/ambient/material scenarios or a worst case, with robust constraint
gradients checked against finite differences. The fully nonlinear bonus plus
uncertainty would provide an independent +10 path; topology can remain a third
bonus attempt under the +15 cap.

## Human approval

> We approve DEC-002: 55 mm height cap, linear comparison h = 15 W/(m² K), and
> the uncertainty bonus as the backup path to at least +10.

The approval was received on 2026-11-11. The authoritative specification and
configuration now include these values. The team also confirmed Kellen
Worthington as a Project 4 author.

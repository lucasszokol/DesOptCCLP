# Optimization and topology campaign

Status: **complete_with_authoritative_model_blockers**

Campaign runtime: 24.970 s.

## Runs

| Run | Role | Method | Success | Accepted | Mass (kg) | Max scaled constraint | Iterations | Time (s) |
|---|---|---|:---:|:---:|---:|---:|---:|---:|
| linear_fixed_topology | linear_fixed_reference | SLSQP | FAIL | FAIL | 0.17615 | 0.0310537 | 62 | 15.713 |
| nonlinear_fixed_uniform_max | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1733531364 | -6.43929e-15 | 9 | 0.836 |
| nonlinear_fixed_uniform_75_percent | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1733531364 | -1.33227e-15 | 17 | 1.742 |
| nonlinear_fixed_symmetric_taper | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1733531364 | 5.28244e-13 | 11 | 1.041 |
| topology_start_from_fixed_topology_p1 | topology_start | SLSQP | PASS | PASS | 0.1733531364 | -6.43929e-15 | 1 | 0.070 |
| topology_start_uniform_density_0p60_p1 | topology_start | SLSQP | PASS | PASS | 0.1733531364 | 1.23368e-12 | 12 | 1.042 |
| topology_start_edge_weighted_density_p1 | topology_start | SLSQP | PASS | PASS | 0.1733531364 | 2.6712e-13 | 11 | 0.916 |
| topology_simp_p2 | simp_continuation | SLSQP | PASS | PASS | 0.1733531364 | -6.43929e-15 | 1 | 0.072 |
| topology_simp_p3 | simp_continuation | SLSQP | PASS | PASS | 0.1733531364 | -6.43929e-15 | 1 | 0.071 |
| threshold_height_reoptimization | threshold_height_reoptimization | SLSQP | PASS | PASS | 0.1733531364 | -6.43929e-15 | 1 | 0.070 |
| trust_constr_kkt_polish | kkt_polish | trust-constr | PASS | PASS | 0.1733531519 | -6.50673e-10 | 50 | 3.187 |

## Comparisons

- Linear fixed-topology feasibility: **False** (maximum scaled constraint 0.0310537).
- Nonlinear fixed-topology mass: 0.1733531364 kg.
- Final topology-continuation mass: 0.1733531364 kg.
- Thresholded/re-optimized mass: 0.1733531364 kg.
- KKT-polished mass: 0.1733531519 kg.
- Topology mass change relative to nonlinear fixed topology: 0 kg (0.000000%).

## Topology

- Active fins after threshold: 20 / 20.
- Intermediate raw densities in (0.01, 0.99): 0.
- Intermediate filtered densities after thresholding: 0.
- Grayness metric: 0.
- Topology bonus demonstrated by a vanished fin: **False**.
- Any single-fin deletion feasible at maximum height: **False**.

## KKT evidence

- Physical stationarity infinity norm: 1.6094328097334578e-09.
- Constraint complementarity infinity norm: 1.0239999896742565e-08.
- Bound complementarity infinity norm: 1.0763881582399319e-08.
- Constraint violation: 0.0.

| Active constraint | Scaled value | Normalized multiplier | kg per unit scaled relaxation |
|---|---:|---:|---:|
| overload | -6.50673e-10 | 14.7255 | 1.79578 |

The linear fixed-topology reference is retained as an unsuccessful, infeasible baseline because the maximum-material linear design violates the frozen temperature limits. It is not relabeled as a successful optimum.

No topology bonus is claimed: all twenty fins remain active, and the generated one-fin-removal screen found every deletion infeasible at the maximum height. Changing the height or physics assumptions requires a human-approved shared-contract update outside Agent 3's scope.

All values in this report are generated from `campaign.json` by the campaign command.

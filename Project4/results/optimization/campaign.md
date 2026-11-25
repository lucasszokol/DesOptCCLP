# Optimization and topology campaign

Status: **complete_with_authoritative_model_blockers**

Campaign runtime: 77.302 s.

## Runs

| Run | Role | Method | Success | Accepted | Mass (kg) | Max scaled constraint | Iterations | Time (s) |
|---|---|---|:---:|:---:|---:|---:|---:|---:|
| linear_fixed_topology | linear_fixed_reference | SLSQP | PASS | PASS | 0.152513423 | 3.62483e-11 | 17 | 2.976 |
| nonlinear_fixed_uniform_max | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1773042727 | 3.07452e-12 | 15 | 5.572 |
| nonlinear_fixed_uniform_75_percent | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1773042726 | 1.91134e-11 | 13 | 6.315 |
| nonlinear_fixed_symmetric_taper | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1773042727 | 9.97073e-13 | 13 | 6.546 |
| topology_start_from_fixed_topology_p1 | topology_start | SLSQP | PASS | PASS | 0.1773042727 | 3.454e-12 | 1 | 1.102 |
| topology_start_uniform_density_0p60_p1 | topology_start | SLSQP | PASS | PASS | 0.1773042727 | -6.9016e-15 | 30 | 21.447 |
| topology_start_edge_weighted_density_p1 | topology_start | SLSQP | PASS | PASS | 0.1773042726 | 4.56484e-11 | 13 | 5.137 |
| topology_simp_p2 | simp_continuation | SLSQP | PASS | PASS | 0.1773042727 | 3.43845e-12 | 1 | 1.945 |
| topology_simp_p3 | simp_continuation | SLSQP | PASS | PASS | 0.1773042727 | 3.44978e-12 | 1 | 2.907 |
| threshold_height_reoptimization | threshold_height_reoptimization | SLSQP | PASS | PASS | 0.1773042727 | 3.46787e-12 | 1 | 2.935 |
| trust_constr_kkt_polish | kkt_polish | trust-constr | PASS | PASS | 0.177304273 | -2.41274e-11 | 78 | 20.169 |

## Comparisons

- Linear fixed-topology feasibility: **True** (maximum buffered scaled constraint 3.62483e-11).
- Nonlinear fixed-topology mass: 0.1773042727 kg.
- Final topology-continuation mass: 0.1773042727 kg.
- Thresholded/re-optimized mass: 0.1773042727 kg.
- KKT-polished mass: 0.177304273 kg.
- Topology mass change relative to nonlinear fixed topology: -1.74416e-12 kg (-0.000000%).

## Topology

- Active fins after threshold: 20 / 20.
- Intermediate raw densities in (0.01, 0.99): 0.
- Intermediate filtered densities after thresholding: 0.
- Grayness metric: 0.
- Topology bonus demonstrated by a vanished fin: **False**.
- Any filtered single-low-raw-density screen feasible at maximum height: **True** (not a discrete removed-fin result).

## KKT evidence

- Physical stationarity infinity norm: 2.1672321804664475e-10.
- Constraint complementarity infinity norm: 4.095999760051005e-10.
- Bound complementarity infinity norm: 4.075634533408367e-10.
- Constraint violation: 0.0.

| Active constraint | Raw scaled value | Buffered scaled value | Normalized multiplier | kg per unit scaled relaxation |
|---|---:|---:|---:|---:|
| overload | -0.00133994 | -2.41274e-11 | 14.7377 | 1.79726 |

The filtered screen lowers one raw density and retains the density filter; it is not a reanalysis of a physically removed fin. Interpret the results accordingly and do not claim a vanished-fin bonus without a feasible discrete reanalysis.

All values in this report are generated from `campaign.json` by the campaign command.

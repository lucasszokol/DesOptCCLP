# Optimization and topology campaign

Status: **complete_with_authoritative_model_blockers**

Campaign runtime: 74.807 s.

## Runs

| Run | Role | Method | Success | Accepted | Mass (kg) | Max scaled constraint | Iterations | Time (s) |
|---|---|---|:---:|:---:|---:|---:|---:|---:|
| linear_fixed_topology | linear_fixed_reference | SLSQP | PASS | PASS | 0.1497443198 | 3.85469e-13 | 18 | 3.780 |
| nonlinear_fixed_uniform_max | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1727902237 | 7.0961e-12 | 14 | 7.532 |
| nonlinear_fixed_uniform_75_percent | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1727902237 | 1.77491e-11 | 14 | 8.352 |
| nonlinear_fixed_symmetric_taper | nonlinear_fixed_start | SLSQP | PASS | PASS | 0.1727902237 | 1.17255e-11 | 14 | 8.112 |
| topology_start_from_fixed_topology_p1 | topology_start | SLSQP | PASS | PASS | 0.1727902237 | 6.91558e-12 | 1 | 0.933 |
| topology_start_uniform_density_0p60_p1 | topology_start | SLSQP | PASS | PASS | 0.1727902237 | 8.13793e-13 | 16 | 7.635 |
| topology_start_edge_weighted_density_p1 | topology_start | SLSQP | PASS | PASS | 0.1727902237 | 7.20979e-12 | 14 | 6.801 |
| topology_simp_p2 | simp_continuation | SLSQP | PASS | PASS | 0.1727902237 | 6.63736e-12 | 1 | 1.225 |
| topology_simp_p3 | simp_continuation | SLSQP | PASS | PASS | 0.1727902237 | 5.97566e-12 | 1 | 0.900 |
| threshold_height_reoptimization | threshold_height_reoptimization | SLSQP | PASS | PASS | 0.1727902237 | 5.75007e-12 | 1 | 1.186 |
| trust_constr_kkt_polish | kkt_polish | trust-constr | PASS | PASS | 0.172790224 | -3.13153e-11 | 83 | 28.054 |

## Comparisons

- Linear fixed-topology feasibility: **True** (maximum scaled constraint 3.85469e-13).
- Nonlinear fixed-topology mass: 0.1727902237 kg.
- Final topology-continuation mass: 0.1727902237 kg.
- Thresholded/re-optimized mass: 0.1727902237 kg.
- KKT-polished mass: 0.172790224 kg.
- Topology mass change relative to nonlinear fixed topology: 1.52831e-12 kg (0.000000%).

## Topology

- Active fins after threshold: 20 / 20.
- Intermediate raw densities in (0.01, 0.99): 0.
- Intermediate filtered densities after thresholding: 0.
- Grayness metric: 0.
- Topology bonus demonstrated by a vanished fin: **False**.
- Any single-fin deletion feasible at maximum height: **True**.

## KKT evidence

- Physical stationarity infinity norm: 2.18236350397555e-09.
- Constraint complementarity infinity norm: 4.2674924841142157e-10.
- Bound complementarity infinity norm: 6.23706330487983e-10.
- Constraint violation: 0.0.

| Active constraint | Scaled value | Normalized multiplier | kg per unit scaled relaxation |
|---|---:|---:|---:|
| overload | -3.13153e-11 | 13.6275 | 1.66187 |

The single-fin screen lowers one raw density and retains the density filter; it is not a reanalysis of a physically removed fin. Interpret the results accordingly and do not claim a vanished-fin bonus without a feasible discrete reanalysis.

All values in this report are generated from `campaign.json` by the campaign command.

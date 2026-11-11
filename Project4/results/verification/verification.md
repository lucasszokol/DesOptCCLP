# Verification evidence

Status: **PASSED** (20/20 checks passed).

Regenerate from the repository root:

```powershell
.\.venv\Scripts\python.exe -m Project4.heatsink.benchmark_verification --config Project4\config.yaml
```

| ID | Quantity | Computed | Submitted/exact | Abs. error | Tolerance | Pass |
|---|---|---:|---:|---:|---:|:---:|
| V1 | T(1/4L) | 353.15 | 353.15 | 0 | 5e-09 | PASS |
| V1 | T(1/2L) | 333.15 | 333.15 | 5.68e-14 | 5e-09 | PASS |
| V1 | T(3/4L) | 313.15 | 313.15 | 0 | 5e-09 | PASS |
| V1 | outward heat rate | 16.7 | 16.7 | 1.78e-14 | 5e-09 | PASS |
| V2 | m | 11.05240646 | 11.052 | 0.000406 | 0.0005 | PASS |
| V2 | tip temperature | 345.7023332 | 345.702 | 0.000333 | 0.0005 | PASS |
| V2 | base heat rate | 2.55050602 | 2.551 | 0.000494 | 0.0005 | PASS |
| V3 | energy-norm convergence slope | 0.9946297069 | 1 | 0.00537 | 0.12 | PASS |
| V3 | L2 convergence slope | 1.99536135 | 2 | 0.00464 | 0.15 | PASS |
| V4 | nominal linear energy balance | 1.231086344e-12 | 0 | 1.23e-12 | 1e-08 | PASS |
| V4 | nominal nonlinear energy balance | 1.260929139e-12 | 0 | 1.26e-12 | 1e-08 | PASS |
| V4 | overload linear energy balance | 1.122302251e-12 | 0 | 1.12e-12 | 1e-08 | PASS |
| V4 | overload nonlinear energy balance | 3.830535888e-12 | 0 | 3.83e-12 | 1e-08 | PASS |
| V5 | reflection/permutation max error K | 2.040678737e-11 | 0 | 2.04e-11 | 2e-09 | PASS |
| V5 | SI/mm line-matrix max error W/K | 0 | 0 | 0 | 1e-12 | PASS |
| V6 | equilibrium temperature | 359.1885105 | 359.19 | 0.00149 | 0.005 | PASS |
| V6 | Newton T1 | 359.4693657 | 359.471 | 0.00163 | 0.002 | PASS |
| V6 | Newton T2 | 359.1887562 | 359.1903 | 0.00154 | 0.002 | PASS |
| V6 | Newton T3 | 359.1885105 | 359.19 | 0.00149 | 0.002 | PASS |
| V6 | analytic tangent vs finite difference | 0.1666952969 | 0.1666952968 | 3.73e-11 | 1e-09 | PASS |

# V7 adjoint and sensitivity evidence

Status: **PASSED**

| Response | Variable family | Taylor slope | Best relative directional error | Pass |
|---|---|---:|---:|:---:|
| nominal constraint | height | 1.98133 | 9.9e-09 | PASS |
| nominal constraint | density | 2.0684 | 1.98e-09 | PASS |
| overload constraint | height | 1.98127 | 9.19e-10 | PASS |
| overload constraint | density | 2.06745 | 5.02e-09 | PASS |

| Objective | Variable family | Relative error | Pass |
|---|---|---:|:---:|
| mass | height | 4.84e-11 | PASS |
| mass | density | 1.51e-10 | PASS |

Adjoint/finite-difference relative gradient error: `2.27898e-08`.
Measured speedup: `75.9x` (80 central-difference state solves).

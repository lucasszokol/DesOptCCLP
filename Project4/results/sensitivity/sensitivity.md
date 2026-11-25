# V7 adjoint and sensitivity evidence

Status: **PASSED**

The fixed slope window uses the largest four steps, selected before observing errors. All smaller steps are retained in JSON to expose cancellation/roundoff. No tolerance is fitted to results.

| Physics / p | Response | Direction | Variable family | Taylor slope | Best relative directional error | Pass |
|---|---|---|---|---:|---:|:---:|
| linear / 1.0 | nominal constraint | structured | height | 1.98098 | 1.62e-09 | PASS |
| linear / 1.0 | nominal constraint | structured | density | 2.06672 | 7e-10 | PASS |
| linear / 1.0 | nominal constraint | random_0 | height | 1.998 | 1e-11 | PASS |
| linear / 1.0 | nominal constraint | random_0 | density | 1.99017 | 1.45e-09 | PASS |
| linear / 1.0 | nominal constraint | random_1 | height | 2.00056 | 1.6e-09 | PASS |
| linear / 1.0 | nominal constraint | random_1 | density | 1.98644 | 2.37e-09 | PASS |
| linear / 1.0 | overload constraint | structured | height | 1.98098 | 1.45e-09 | PASS |
| linear / 1.0 | overload constraint | structured | density | 2.06673 | 7.9e-10 | PASS |
| linear / 1.0 | overload constraint | random_0 | height | 1.998 | 7.88e-11 | PASS |
| linear / 1.0 | overload constraint | random_0 | density | 1.99016 | 1.43e-09 | PASS |
| linear / 1.0 | overload constraint | random_1 | height | 2.00056 | 1.37e-09 | PASS |
| linear / 1.0 | overload constraint | random_1 | density | 1.98643 | 2.35e-09 | PASS |
| linear / 2.0 | nominal constraint | structured | height | 1.98071 | 5.1e-10 | PASS |
| linear / 2.0 | nominal constraint | structured | density | 2.07169 | 6.26e-10 | PASS |
| linear / 2.0 | nominal constraint | random_0 | height | 1.99828 | 1.33e-08 | PASS |
| linear / 2.0 | nominal constraint | random_0 | density | 1.99112 | 2.88e-10 | PASS |
| linear / 2.0 | nominal constraint | random_1 | height | 2.00069 | 4.58e-09 | PASS |
| linear / 2.0 | nominal constraint | random_1 | density | 1.98731 | 4.71e-10 | PASS |
| linear / 2.0 | overload constraint | structured | height | 1.9807 | 6.22e-10 | PASS |
| linear / 2.0 | overload constraint | structured | density | 2.07171 | 6.99e-10 | PASS |
| linear / 2.0 | overload constraint | random_0 | height | 1.99829 | 1.4e-08 | PASS |
| linear / 2.0 | overload constraint | random_0 | density | 1.99111 | 2.59e-10 | PASS |
| linear / 2.0 | overload constraint | random_1 | height | 2.00069 | 4.11e-09 | PASS |
| linear / 2.0 | overload constraint | random_1 | density | 1.9873 | 5.14e-10 | PASS |
| linear / 3.0 | nominal constraint | structured | height | 1.9801 | 1.07e-09 | PASS |
| linear / 3.0 | nominal constraint | structured | density | 2.08675 | 9.35e-10 | PASS |
| linear / 3.0 | nominal constraint | random_0 | height | 1.99904 | 1.51e-09 | PASS |
| linear / 3.0 | nominal constraint | random_0 | density | 1.99007 | 9.87e-10 | PASS |
| linear / 3.0 | nominal constraint | random_1 | height | 2.00103 | 6.76e-09 | PASS |
| linear / 3.0 | nominal constraint | random_1 | density | 1.98547 | 1.4e-10 | PASS |
| linear / 3.0 | overload constraint | structured | height | 1.9801 | 1.06e-09 | PASS |
| linear / 3.0 | overload constraint | structured | density | 2.08677 | 1.23e-09 | PASS |
| linear / 3.0 | overload constraint | random_0 | height | 1.99905 | 1.56e-09 | PASS |
| linear / 3.0 | overload constraint | random_0 | density | 1.99006 | 1.18e-09 | PASS |
| linear / 3.0 | overload constraint | random_1 | height | 2.00103 | 6.36e-09 | PASS |
| linear / 3.0 | overload constraint | random_1 | density | 1.98545 | 1.19e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | height | 1.98357 | 1.56e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | density | 2.05644 | 6.61e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | height | 1.99821 | 8.52e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | density | 1.99093 | 3.79e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | height | 2.00054 | 2.14e-08 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | density | 1.98774 | 1.64e-09 | PASS |
| nonlinear / 1.0 | overload constraint | structured | height | 1.98368 | 1.78e-10 | PASS |
| nonlinear / 1.0 | overload constraint | structured | density | 2.05587 | 1.1e-09 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | height | 1.99828 | 1.61e-08 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | density | 1.99088 | 1.96e-09 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | height | 2.00056 | 2.24e-08 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | density | 1.98772 | 3.88e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | height | 1.98321 | 6.93e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | density | 2.06378 | 5.06e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | height | 1.99872 | 3.29e-08 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | density | 1.99298 | 1.58e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | height | 2.00078 | 7.02e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | density | 1.98966 | 6.91e-10 | PASS |
| nonlinear / 2.0 | overload constraint | structured | height | 1.98327 | 9.93e-10 | PASS |
| nonlinear / 2.0 | overload constraint | structured | density | 2.06339 | 4.71e-10 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | height | 1.99884 | 2.44e-09 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | density | 1.99333 | 5.87e-09 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | height | 2.00084 | 1.93e-08 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | density | 1.99005 | 1.83e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | height | 1.98245 | 2.15e-11 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | density | 2.07582 | 8.81e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | height | 1.99983 | 9.22e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | density | 1.99761 | 6.91e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | height | 2.00126 | 5.78e-08 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | density | 1.99326 | 1.3e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | height | 1.98242 | 1.74e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | density | 2.07406 | 2.86e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | height | 2.00004 | 1.58e-08 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | density | 1.99991 | 2.43e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | height | 2.00137 | 6.96e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | density | 1.99549 | 5.69e-10 | PASS |

| Objective | Direction | Variable family | Relative error | Pass |
|---|---|---|---:|:---:|
| mass | structured | height | 1.49e-11 | PASS |
| mass | structured | density | 2.13e-14 | PASS |
| mass | random_0 | height | 6.62e-10 | PASS |
| mass | random_0 | density | 8.25e-11 | PASS |
| mass | random_1 | height | 7.77e-13 | PASS |
| mass | random_1 | density | 2.85e-10 | PASS |

| KS state | Relative derivative error | Pass |
|---|---:|:---:|
| uniform_tie | 7.78308e-09 | PASS |
| nonuniform | 3.25679e-09 | PASS |
| large_offset | 2.88215e-09 | PASS |

| Physics | Load | Full-gradient relative error | State + adjoint (s) | State-only FD (s) | Speedup |
|---|---|---:|---:|---:|---:|
| linear | nominal | 3.83449e-08 | 0.04315 | 2.305 | 53.4 |
| linear | overload | 3.995e-08 | 0.04369 | 2.27 | 52 |
| nonlinear | nominal | 1.56862e-07 | 0.1223 | 8.783 | 71.8 |
| nonlinear | overload | 1.26047e-07 | 0.1502 | 10.32 | 68.7 |

Finite differences compute no adjoints. Timings are single warmed measurements, not a portable performance guarantee. Mass is state independent, so its exact direct gradient needs no adjoint solve.

Adjoint/finite-difference relative gradient error: `1.56862e-07`.
Measured speedup: `71.8x` (80 central-difference state solves).

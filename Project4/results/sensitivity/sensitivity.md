# V7 adjoint and sensitivity evidence

Status: **PASSED**

The fixed slope window uses the largest four steps, selected before observing errors. All smaller steps are retained in JSON to expose cancellation/roundoff. No tolerance is fitted to results.

| Physics / p | Response | Direction | Variable family | Taylor slope | Best relative directional error | Pass |
|---|---|---|---|---:|---:|:---:|
| linear / 1.0 | nominal constraint | structured | height | 1.98098 | 3.96e-10 | PASS |
| linear / 1.0 | nominal constraint | structured | density | 2.06671 | 3.86e-10 | PASS |
| linear / 1.0 | nominal constraint | random_0 | height | 1.99799 | 5.52e-09 | PASS |
| linear / 1.0 | nominal constraint | random_0 | density | 1.99018 | 7.46e-11 | PASS |
| linear / 1.0 | nominal constraint | random_1 | height | 2.00056 | 6.09e-09 | PASS |
| linear / 1.0 | nominal constraint | random_1 | density | 1.98645 | 3.56e-11 | PASS |
| linear / 1.0 | overload constraint | structured | height | 1.98098 | 4.47e-10 | PASS |
| linear / 1.0 | overload constraint | structured | density | 2.06672 | 3.87e-10 | PASS |
| linear / 1.0 | overload constraint | random_0 | height | 1.998 | 5.59e-09 | PASS |
| linear / 1.0 | overload constraint | random_0 | density | 1.99017 | 5.08e-11 | PASS |
| linear / 1.0 | overload constraint | random_1 | height | 2.00056 | 6.13e-09 | PASS |
| linear / 1.0 | overload constraint | random_1 | density | 1.98644 | 1.23e-11 | PASS |
| linear / 2.0 | nominal constraint | structured | height | 1.98071 | 7.02e-10 | PASS |
| linear / 2.0 | nominal constraint | structured | density | 2.07168 | 4.5e-10 | PASS |
| linear / 2.0 | nominal constraint | random_0 | height | 1.99828 | 2.15e-09 | PASS |
| linear / 2.0 | nominal constraint | random_0 | density | 1.99113 | 7.45e-10 | PASS |
| linear / 2.0 | nominal constraint | random_1 | height | 2.00069 | 1.46e-09 | PASS |
| linear / 2.0 | nominal constraint | random_1 | density | 1.98732 | 2.41e-10 | PASS |
| linear / 2.0 | overload constraint | structured | height | 1.98071 | 6.54e-10 | PASS |
| linear / 2.0 | overload constraint | structured | density | 2.07169 | 4.58e-10 | PASS |
| linear / 2.0 | overload constraint | random_0 | height | 1.99828 | 2.08e-09 | PASS |
| linear / 2.0 | overload constraint | random_0 | density | 1.99112 | 8.44e-10 | PASS |
| linear / 2.0 | overload constraint | random_1 | height | 2.00069 | 1.68e-09 | PASS |
| linear / 2.0 | overload constraint | random_1 | density | 1.98731 | 2.54e-10 | PASS |
| linear / 3.0 | nominal constraint | structured | height | 1.9801 | 1e-09 | PASS |
| linear / 3.0 | nominal constraint | structured | density | 2.08674 | 2.82e-10 | PASS |
| linear / 3.0 | nominal constraint | random_0 | height | 1.99903 | 8.94e-10 | PASS |
| linear / 3.0 | nominal constraint | random_0 | density | 1.99008 | 3.65e-10 | PASS |
| linear / 3.0 | nominal constraint | random_1 | height | 2.00104 | 5.82e-09 | PASS |
| linear / 3.0 | nominal constraint | random_1 | density | 1.98548 | 1.64e-10 | PASS |
| linear / 3.0 | overload constraint | structured | height | 1.9801 | 9.5e-10 | PASS |
| linear / 3.0 | overload constraint | structured | density | 2.08675 | 2.57e-10 | PASS |
| linear / 3.0 | overload constraint | random_0 | height | 1.99904 | 8.63e-10 | PASS |
| linear / 3.0 | overload constraint | random_0 | density | 1.99008 | 2.89e-10 | PASS |
| linear / 3.0 | overload constraint | random_1 | height | 2.00104 | 6.34e-09 | PASS |
| linear / 3.0 | overload constraint | random_1 | density | 1.98547 | 1.22e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | height | 1.98357 | 4.07e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | density | 2.05643 | 2.94e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | height | 1.99821 | 5.37e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | density | 1.99095 | 2.59e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | height | 2.00055 | 4.41e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | density | 1.98776 | 3.35e-09 | PASS |
| nonlinear / 1.0 | overload constraint | structured | height | 1.98368 | 4.48e-09 | PASS |
| nonlinear / 1.0 | overload constraint | structured | density | 2.05585 | 7.67e-10 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | height | 1.99827 | 2.88e-08 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | density | 1.9909 | 1.66e-09 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | height | 2.00056 | 2.37e-10 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | density | 1.98774 | 1.28e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | height | 1.98322 | 7.41e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | density | 2.06377 | 2.42e-10 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | height | 1.99871 | 9.12e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | density | 1.993 | 7.83e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | height | 2.00079 | 4.6e-08 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | density | 1.98968 | 3.19e-09 | PASS |
| nonlinear / 2.0 | overload constraint | structured | height | 1.98328 | 4.53e-10 | PASS |
| nonlinear / 2.0 | overload constraint | structured | density | 2.06337 | 3.72e-09 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | height | 1.99883 | 2.58e-08 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | density | 1.99336 | 8.4e-12 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | height | 2.00084 | 4.82e-08 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | density | 1.99008 | 9.28e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | height | 1.98245 | 1.02e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | density | 2.0758 | 1.6e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | height | 1.99982 | 6.32e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | density | 1.99763 | 2.03e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | height | 2.00127 | 1.8e-08 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | density | 1.99329 | 1.44e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | height | 1.98242 | 5.18e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | density | 2.07403 | 2.51e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | height | 2.00004 | 4.02e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | density | 1.99994 | 5.19e-10 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | height | 2.00137 | 1.29e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | density | 1.99553 | 2.06e-10 | PASS |

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
| uniform_tie | 8.24707e-09 | PASS |
| nonuniform | 3.28146e-09 | PASS |
| large_offset | 3.62465e-09 | PASS |

| Physics | Load | Full-gradient relative error | State + adjoint (s) | State-only FD (s) | Speedup |
|---|---|---:|---:|---:|---:|
| linear | nominal | 7.27206e-09 | 0.06924 | 3.836 | 55.4 |
| linear | overload | 7.62499e-09 | 0.06496 | 3.377 | 52 |
| nonlinear | nominal | 9.60543e-08 | 0.1788 | 12.45 | 69.6 |
| nonlinear | overload | 1.12038e-07 | 0.2037 | 14.89 | 73.1 |

Finite differences compute no adjoints. Timings are single warmed measurements, not a portable performance guarantee. Mass is state independent, so its exact direct gradient needs no adjoint solve.

Adjoint/finite-difference relative gradient error: `9.60543e-08`.
Measured speedup: `69.6x` (80 central-difference state solves).

# V7 adjoint and sensitivity evidence

Status: **PASSED**

The fixed slope window uses the largest four steps, selected before observing errors. All smaller steps are retained in JSON to expose cancellation/roundoff. No tolerance is fitted to results.

| Physics / p | Response | Direction | Variable family | Taylor slope | Best relative directional error | Pass |
|---|---|---|---|---:|---:|:---:|
| linear / 1.0 | nominal constraint | structured | height | 1.98112 | 4.16e-12 | PASS |
| linear / 1.0 | nominal constraint | structured | density | 2.0668 | 4.72e-10 | PASS |
| linear / 1.0 | nominal constraint | random_0 | height | 1.99786 | 3.88e-09 | PASS |
| linear / 1.0 | nominal constraint | random_0 | density | 1.9904 | 8.26e-10 | PASS |
| linear / 1.0 | nominal constraint | random_1 | height | 2.00062 | 3.74e-09 | PASS |
| linear / 1.0 | nominal constraint | random_1 | density | 1.98664 | 1.17e-09 | PASS |
| linear / 1.0 | overload constraint | structured | height | 1.98112 | 1.65e-10 | PASS |
| linear / 1.0 | overload constraint | structured | density | 2.0668 | 4.99e-10 | PASS |
| linear / 1.0 | overload constraint | random_0 | height | 1.99786 | 4.15e-09 | PASS |
| linear / 1.0 | overload constraint | random_0 | density | 1.9904 | 8.18e-10 | PASS |
| linear / 1.0 | overload constraint | random_1 | height | 2.00062 | 4e-09 | PASS |
| linear / 1.0 | overload constraint | random_1 | density | 1.98663 | 1.22e-09 | PASS |
| linear / 2.0 | nominal constraint | structured | height | 1.98098 | 6.79e-10 | PASS |
| linear / 2.0 | nominal constraint | structured | density | 2.07077 | 1.27e-09 | PASS |
| linear / 2.0 | nominal constraint | random_0 | height | 1.99802 | 5.92e-09 | PASS |
| linear / 2.0 | nominal constraint | random_0 | density | 1.99079 | 1.1e-09 | PASS |
| linear / 2.0 | nominal constraint | random_1 | height | 2.00068 | 9.82e-10 | PASS |
| linear / 2.0 | nominal constraint | random_1 | density | 1.98693 | 5.42e-10 | PASS |
| linear / 2.0 | overload constraint | structured | height | 1.98098 | 6.44e-10 | PASS |
| linear / 2.0 | overload constraint | structured | density | 2.07078 | 1.29e-09 | PASS |
| linear / 2.0 | overload constraint | random_0 | height | 1.99802 | 6.05e-09 | PASS |
| linear / 2.0 | overload constraint | random_0 | density | 1.99079 | 1.08e-09 | PASS |
| linear / 2.0 | overload constraint | random_1 | height | 2.00068 | 1.37e-09 | PASS |
| linear / 2.0 | overload constraint | random_1 | density | 1.98692 | 5.28e-10 | PASS |
| linear / 3.0 | nominal constraint | structured | height | 1.98066 | 1.67e-09 | PASS |
| linear / 3.0 | nominal constraint | structured | density | 2.08594 | 9.53e-10 | PASS |
| linear / 3.0 | nominal constraint | random_0 | height | 1.9985 | 3.01e-09 | PASS |
| linear / 3.0 | nominal constraint | random_0 | density | 1.98698 | 2.87e-10 | PASS |
| linear / 3.0 | nominal constraint | random_1 | height | 2.00088 | 1.06e-08 | PASS |
| linear / 3.0 | nominal constraint | random_1 | density | 1.98225 | 7.16e-10 | PASS |
| linear / 3.0 | overload constraint | structured | height | 1.98066 | 1.69e-09 | PASS |
| linear / 3.0 | overload constraint | structured | density | 2.08595 | 9.56e-10 | PASS |
| linear / 3.0 | overload constraint | random_0 | height | 1.9985 | 3.25e-09 | PASS |
| linear / 3.0 | overload constraint | random_0 | density | 1.98697 | 2.58e-10 | PASS |
| linear / 3.0 | overload constraint | random_1 | height | 2.00088 | 1.08e-08 | PASS |
| linear / 3.0 | overload constraint | random_1 | density | 1.98224 | 7.18e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | height | 1.98357 | 4.07e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | structured | density | 2.05643 | 2.94e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | height | 1.99821 | 5.37e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_0 | density | 1.99095 | 2.59e-09 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | height | 2.00055 | 4.41e-10 | PASS |
| nonlinear / 1.0 | nominal constraint | random_1 | density | 1.98776 | 3.35e-09 | PASS |
| nonlinear / 1.0 | overload constraint | structured | height | 1.98368 | 4.48e-09 | PASS |
| nonlinear / 1.0 | overload constraint | structured | density | 2.05585 | 1.06e-11 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | height | 1.99827 | 2.88e-08 | PASS |
| nonlinear / 1.0 | overload constraint | random_0 | density | 1.9909 | 1.66e-09 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | height | 2.00056 | 1.88e-08 | PASS |
| nonlinear / 1.0 | overload constraint | random_1 | density | 1.98774 | 1.28e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | height | 1.98322 | 7.41e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | structured | density | 2.06377 | 2.42e-10 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | height | 1.99871 | 9.12e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_0 | density | 1.993 | 7.6e-09 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | height | 2.00079 | 2.91e-08 | PASS |
| nonlinear / 2.0 | nominal constraint | random_1 | density | 1.98968 | 3.46e-09 | PASS |
| nonlinear / 2.0 | overload constraint | structured | height | 1.98328 | 2.58e-09 | PASS |
| nonlinear / 2.0 | overload constraint | structured | density | 2.06337 | 3.72e-09 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | height | 1.99883 | 2.58e-08 | PASS |
| nonlinear / 2.0 | overload constraint | random_0 | density | 1.99336 | 8.4e-12 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | height | 2.00084 | 4.82e-08 | PASS |
| nonlinear / 2.0 | overload constraint | random_1 | density | 1.99008 | 9.28e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | height | 1.98245 | 1.02e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | structured | density | 2.0758 | 1.91e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | height | 1.99982 | 6.32e-09 | PASS |
| nonlinear / 3.0 | nominal constraint | random_0 | density | 1.99763 | 2.03e-10 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | height | 2.00127 | 1.8e-08 | PASS |
| nonlinear / 3.0 | nominal constraint | random_1 | density | 1.99329 | 2.01e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | height | 1.98242 | 5.18e-09 | PASS |
| nonlinear / 3.0 | overload constraint | structured | density | 2.07403 | 2.51e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | height | 2.00004 | 4.02e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_0 | density | 1.99994 | 1.07e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | height | 2.00137 | 1.29e-09 | PASS |
| nonlinear / 3.0 | overload constraint | random_1 | density | 1.99553 | 1.72e-10 | PASS |

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
| linear | nominal | 7.75756e-09 | 0.0266 | 1.391 | 52.3 |
| linear | overload | 7.82735e-09 | 0.04266 | 1.461 | 34.3 |
| nonlinear | nominal | 9.28936e-08 | 0.071 | 4.82 | 67.9 |
| nonlinear | overload | 1.13527e-07 | 0.08215 | 5.709 | 69.5 |

Finite differences compute no adjoints. Timings are single warmed measurements, not a portable performance guarantee. Mass is state independent, so its exact direct gradient needs no adjoint solve.

Adjoint/finite-difference relative gradient error: `9.28936e-08`.
Measured speedup: `67.9x` (80 central-difference state solves).

# Human Verification Worksheet — Setups Only

Complete this worksheet without asking a coding agent to calculate the expected
answers. Return the formulas and numerical results to the implementation chat.
The numbers will then be transcribed into `tests/benchmark_truth.yaml`, with the
student derivation retained in the report appendix.

Use SI units and at least eight significant digits in intermediate work.

## V1 — One-dimensional conduction bar

A uniform bar has length `L = 0.040 m`, area `A = 5.0e-5 m²`, and conductivity
`k = 167 W/(m K)`. Set `T(0) = 373.15 K` and `T(L) = 293.15 K` with no internal
generation.

Provide:

1. The exact expression for `T(x)`.
2. `T(L/4)`, `T(L/2)`, and `T(3L/4)` in kelvin.
3. The signed heat rate at `x = L` using the outward-normal convention.

## V2 — Straight fin with convection

An untipped rectangular fin has `L = 0.050 m`, `k = 167 W/(m K)`, width
`d = 0.050 m`, thickness `t = 0.001 m`, constant `h = 10 W/(m² K)`, base
temperature `T_b = 353.15 K`, and ambient `T_inf = 298.15 K`. Use an adiabatic
tip for this benchmark.

Provide:

1. The exact excess-temperature expression `theta(x)`.
2. The parameter `m = sqrt(h P/(k A))` with `P = 2(d+t)` and `A = dt`.
3. Tip temperature and base heat rate.

## V3 — Manufactured two-dimensional solution

On the unit square, use conductivity `k = 1 W/(m K)` and prescribe

`T(x,z) = 300 + sin(pi*x) sin(pi*z)` K

on the boundary and throughout the domain by choosing the necessary volumetric
source in `-div(k grad T) = q`.

Provide:

1. The exact source `q(x,z)` including its sign.

   `q(x,z) = 2k(pi)^2 sin(pi*x) sin(pi*z)`
   The sign is positive.
3. The expected asymptotic slope for the nodal/energy error selected for
   bilinear quadrilateral elements; state which norm the slope applies to.

## V6 — Nonlinear single-surface balance

A lumped isothermal surface has area `A = 0.010 m²`, ambient `T_inf = 298.15 K`,
input `Q = 8 W`, emissivity `epsilon = 0.80`, and

`h(T) = 5 * ((T - T_inf)/20)^(1/4) W/(m² K)` for `T > T_inf`.

Its equilibrium is

`A [ h(T)(T-T_inf) + epsilon*sigma*(T^4-T_inf^4) ] - Q = 0`.

Provide:

1. The equilibrium temperature in kelvin.
   `$T_{\eq}$ = 359.19 K`
2. The analytic derivative of the residual with respect to `T` at equilibrium.
   $R'(T) = A\left[2.9554\left(T - T_{\infty}\right)^{1/4} + 4\epsilon\sigma T^3\right]$
3. Three Newton iterates starting from `T0 = 350 K` without line search.
   `T1 = 359.4710 K`
   `T2 = 359.1903 K`
   `T3 = 359.1900 K`
4. A short explanation of what quadratic convergence should look like in the
   residual sequence.
   Near the solution, the next step of the residual is proportional to the previous step squared.
## Student attestation

Names of students who checked the work:
Charlie Green, Kellen Worthington, Polina Kondratiuk, Lucas Somoshegyi-Szokol, Christian Miranda 
Derivation method/reference used:
Heat transfer
Date: 11/11/2026

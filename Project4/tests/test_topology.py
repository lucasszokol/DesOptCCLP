import numpy as np

from heatsink.topology import density_filter, filtered_density, simp_derivative, simp_factor


def test_filter_preserves_constant_density() -> None:
    matrix = density_filter(20, 1.5)
    np.testing.assert_allclose(matrix.sum(axis=1), 1.0)
    np.testing.assert_allclose(filtered_density(np.ones(20), matrix), 1.0)


def test_simp_factor_and_derivative() -> None:
    density = np.array([0.2, 0.7, 1.0])
    derivative = simp_derivative(density, 3.0, 0.001)
    step = 1.0e-7
    finite_difference = (simp_factor(density + step, 3.0, 0.001) - simp_factor(density - step, 3.0, 0.001)) / (2.0 * step)
    np.testing.assert_allclose(derivative, finite_difference, rtol=1.0e-8)

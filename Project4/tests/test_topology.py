import numpy as np
import pytest

from heatsink.topology import (
    density_filter,
    filtered_density,
    grayness,
    intermediate_density_count,
    simp_derivative,
    simp_factor,
    threshold_density,
)


def test_filter_preserves_constant_density() -> None:
    matrix = density_filter(20, 1.5)
    np.testing.assert_allclose(matrix.sum(axis=1), 1.0)
    np.testing.assert_allclose(filtered_density(np.ones(20), matrix), 1.0)


def test_simp_factor_and_derivative() -> None:
    density = np.array([0.2, 0.7, 0.9])
    derivative = simp_derivative(density, 3.0, 0.001)
    step = 1.0e-7
    finite_difference = (simp_factor(density + step, 3.0, 0.001) - simp_factor(density - step, 3.0, 0.001)) / (2.0 * step)
    np.testing.assert_allclose(derivative, finite_difference, rtol=1.0e-8)


def test_threshold_and_discreteness_metrics() -> None:
    raw = np.array([0.001, 0.009, 0.5, 0.991, 1.0])
    binary = threshold_density(raw, threshold=0.5, floor=0.001)
    np.testing.assert_allclose(binary, [0.001, 0.001, 1.0, 1.0, 1.0])
    assert intermediate_density_count(raw) == 1
    assert intermediate_density_count(binary) == 0
    assert grayness(np.array([0.0, 1.0])) == 0.0
    assert grayness(np.array([0.5])) == 1.0


def test_topology_helpers_reject_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        simp_derivative(np.array([0.5]), 0.5, 0.001)
    with pytest.raises(ValueError):
        threshold_density(np.array([0.5]), threshold=0.0, floor=0.001)
    with pytest.raises(ValueError):
        filtered_density(np.ones(3), np.eye(2))

"""Ground-structure density filtering and SIMP interpolation."""

from __future__ import annotations

import numpy as np


def density_filter(count: int, radius: float) -> np.ndarray:
    if count < 1 or radius <= 0.0:
        raise ValueError("count and radius must be positive")
    index = np.arange(count, dtype=float)
    weights = np.maximum(0.0, radius - np.abs(index[:, None] - index[None, :]))
    return weights / weights.sum(axis=1, keepdims=True)


def filtered_density(raw_density: np.ndarray, filter_matrix: np.ndarray) -> np.ndarray:
    return np.asarray(filter_matrix, dtype=float) @ np.asarray(raw_density, dtype=float)


def simp_factor(density: np.ndarray, penalty: float, floor: float) -> np.ndarray:
    if penalty < 1.0 or not 0.0 < floor < 1.0:
        raise ValueError("invalid SIMP parameters")
    rho = np.asarray(density, dtype=float)
    return floor + (1.0 - floor) * rho**penalty


def simp_derivative(density: np.ndarray, penalty: float, floor: float) -> np.ndarray:
    rho = np.asarray(density, dtype=float)
    return (1.0 - floor) * penalty * rho ** (penalty - 1.0)

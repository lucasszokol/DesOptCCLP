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
    matrix = np.asarray(filter_matrix, dtype=float)
    raw = np.asarray(raw_density, dtype=float)
    if matrix.ndim != 2 or matrix.shape[1] != raw.size:
        raise ValueError("filter matrix and raw density have incompatible shapes")
    return matrix @ raw


def simp_factor(density: np.ndarray, penalty: float, floor: float) -> np.ndarray:
    if penalty < 1.0 or not 0.0 < floor < 1.0:
        raise ValueError("invalid SIMP parameters")
    rho = np.asarray(density, dtype=float)
    return floor + (1.0 - floor) * rho**penalty


def simp_derivative(density: np.ndarray, penalty: float, floor: float) -> np.ndarray:
    if penalty < 1.0 or not 0.0 < floor < 1.0:
        raise ValueError("invalid SIMP parameters")
    rho = np.asarray(density, dtype=float)
    return (1.0 - floor) * penalty * rho ** (penalty - 1.0)


def threshold_density(
    raw_density: np.ndarray,
    threshold: float,
    floor: float,
) -> np.ndarray:
    """Return a binary density vector using the configured positive floor."""

    if not 0.0 < floor < threshold < 1.0:
        raise ValueError("require 0 < floor < threshold < 1")
    raw = np.asarray(raw_density, dtype=float)
    if np.any((raw < 0.0) | (raw > 1.0)):
        raise ValueError("density must lie in [0, 1]")
    return np.where(raw >= threshold, 1.0, floor)


def intermediate_density_count(
    density: np.ndarray,
    *,
    lower: float = 0.01,
    upper: float = 0.99,
) -> int:
    """Count density entries outside the near-binary bands."""

    if not 0.0 <= lower < upper <= 1.0:
        raise ValueError("invalid near-binary bounds")
    values = np.asarray(density, dtype=float)
    return int(np.count_nonzero((values > lower) & (values < upper)))


def grayness(density: np.ndarray) -> float:
    """Return the standard mean ``4 rho (1-rho)`` discreteness metric."""

    values = np.asarray(density, dtype=float)
    if values.size == 0 or np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("density must be a non-empty array in [0, 1]")
    return float(np.mean(4.0 * values * (1.0 - values)))

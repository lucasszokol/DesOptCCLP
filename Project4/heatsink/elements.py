"""Finite-element kernels kept independent for verification."""

from __future__ import annotations

import numpy as np


def line_conduction_matrix(k: float, area: float, length: float) -> np.ndarray:
    if k <= 0.0 or area <= 0.0 or length <= 0.0:
        raise ValueError("k, area, and length must be positive")
    return (k * area / length) * np.array([[1.0, -1.0], [-1.0, 1.0]])


def quad4_conduction_matrix(coordinates: np.ndarray, conductivity: float, depth: float) -> np.ndarray:
    """Bilinear quadrilateral conduction matrix using 2×2 Gauss integration."""

    xy = np.asarray(coordinates, dtype=float)
    if xy.shape != (4, 2):
        raise ValueError("coordinates must have shape (4, 2)")
    if conductivity <= 0.0 or depth <= 0.0:
        raise ValueError("conductivity and depth must be positive")
    matrix = np.zeros((4, 4), dtype=float)
    points = (-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))
    for xi in points:
        for eta in points:
            dnatural = 0.25 * np.array([[-(1.0-eta), +(1.0-eta), +(1.0+eta), -(1.0+eta)], [-(1.0-xi), -(1.0+xi), +(1.0+xi), +(1.0-xi)]])
            jacobian = dnatural @ xy
            determinant = float(np.linalg.det(jacobian))
            if determinant <= 0.0:
                raise ValueError("quad element has a non-positive Jacobian")
            gradient = np.linalg.solve(jacobian, dnatural)
            matrix += conductivity * depth * determinant * (gradient.T @ gradient)
    return matrix

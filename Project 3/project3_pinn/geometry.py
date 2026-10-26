from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import GeometryConfig, PINNConfig


LOSS_NAMES = (
    "continuity",
    "momentum_x",
    "momentum_y",
    "inlet",
    "walls",
    "outlet",
)


@dataclass
class TrainingPoints:
    interior: np.ndarray
    inlet: np.ndarray
    walls: np.ndarray
    outlet: np.ndarray


def is_inside_cylinder(points: np.ndarray, geometry: GeometryConfig) -> np.ndarray:
    dx = points[:, 0] - geometry.cylinder_x
    dy = points[:, 1] - geometry.cylinder_y
    return dx * dx + dy * dy <= geometry.cylinder_radius**2


def sample_interior(
    geometry: GeometryConfig, count: int, rng: np.random.Generator
) -> np.ndarray:
    """Sample the fluid domain, reserving one quarter for the near wake."""
    target_wake = count // 4
    target_global = count - target_wake

    def accepted_box(n: int, low: tuple[float, float], high: tuple[float, float]) -> np.ndarray:
        chunks: list[np.ndarray] = []
        found = 0
        while found < n:
            candidate = rng.uniform(low, high, size=(max(2 * (n - found), 128), 2))
            candidate = candidate[~is_inside_cylinder(candidate, geometry)]
            chunks.append(candidate)
            found += candidate.shape[0]
        return np.concatenate(chunks, axis=0)[:n]

    global_points = accepted_box(
        target_global, (0.0, 0.0), (geometry.length, geometry.height)
    )
    wake_points = accepted_box(
        target_wake,
        (max(0.0, geometry.cylinder_x - 0.75), 0.25),
        (min(8.0, geometry.length), geometry.height - 0.25),
    )
    points = np.concatenate((global_points, wake_points), axis=0)
    rng.shuffle(points)
    return points.astype(np.float32)


def sample_training_points(
    geometry: GeometryConfig, pinn: PINNConfig, seed: int
) -> TrainingPoints:
    rng = np.random.default_rng(seed)
    n = pinn.boundary_points
    interior = sample_interior(geometry, pinn.interior_pool, rng)

    y_in = np.linspace(0.0, geometry.height, n, dtype=np.float32)
    inlet = np.column_stack((np.zeros(n, dtype=np.float32), y_in))
    outlet = np.column_stack(
        (np.full(n, geometry.length, dtype=np.float32), y_in)
    )

    n_flat = n // 3
    x_wall = np.linspace(0.0, geometry.length, n_flat, dtype=np.float32)
    bottom = np.column_stack((x_wall, np.zeros(n_flat, dtype=np.float32)))
    top = np.column_stack(
        (x_wall, np.full(n_flat, geometry.height, dtype=np.float32))
    )
    theta = np.linspace(0.0, 2.0 * np.pi, n - 2 * n_flat, endpoint=False)
    cylinder = np.column_stack(
        (
            geometry.cylinder_x + geometry.cylinder_radius * np.cos(theta),
            geometry.cylinder_y + geometry.cylinder_radius * np.sin(theta),
        )
    ).astype(np.float32)
    walls = np.concatenate((bottom, top, cylinder), axis=0)
    return TrainingPoints(interior=interior, inlet=inlet, walls=walls, outlet=outlet)


def inlet_velocity(y: np.ndarray, geometry: GeometryConfig) -> np.ndarray:
    """Parabolic profile with unit cross-sectional mean velocity."""
    return 6.0 * y * (geometry.height - y) / geometry.height**2

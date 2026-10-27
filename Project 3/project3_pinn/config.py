from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeometryConfig:
    length: float = 22.0
    height: float = 4.1
    cylinder_x: float = 2.0
    cylinder_y: float = 2.0
    cylinder_radius: float = 0.5


@dataclass(frozen=True)
class LBMConfig:
    nodes_per_diameter: int = 16
    lattice_mean_velocity: float = 0.05
    max_steps: int = 30_000
    min_steps: int = 2_000
    check_every: int = 250
    convergence_tolerance: float = 1.0e-3
    consecutive_convergence_checks: int = 4
    mass_imbalance_tolerance: float = 1.0e-2
    grid_difference_tolerance: float = 5.0e-2


@dataclass(frozen=True)
class PINNConfig:
    hidden_layers: int = 5
    hidden_width: int = 64
    interior_pool: int = 30_000
    interior_batch: int = 4_096
    boundary_points: int = 768
    adam_steps: int = 12_000
    adam_learning_rate: float = 1.0e-3
    lbfgs_steps: int = 300
    log_every: int = 100
    balance_every: int = 100
    checkpoint_every: int = 1_000
    weight_ema: float = 0.9
    min_weight: float = 0.1
    max_weight: float = 10.0
    supervised_points: int = 20_000
    evaluation_batch: int = 16_384
    dtype: str = "float32"


@dataclass(frozen=True)
class ExperimentConfig:
    reynolds_numbers: tuple[int, ...] = (10, 20, 40)
    seeds: tuple[int, ...] = (0, 1, 2)
    methods: tuple[str, ...] = ("vanilla", "balanced", "supervised")
    geometry: GeometryConfig = field(default_factory=GeometryConfig)
    lbm: LBMConfig = field(default_factory=LBMConfig)
    pinn: PINNConfig = field(default_factory=PINNConfig)
    output_dir: Path = Path("project3_results")

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["output_dir"] = str(self.output_dir)
        return data

    @classmethod
    def quick(cls, output_dir: Path = Path("project3_results_quick")) -> "ExperimentConfig":
        return cls(
            reynolds_numbers=(10,),
            seeds=(0,),
            methods=("vanilla", "balanced", "supervised"),
            lbm=LBMConfig(
                nodes_per_diameter=8,
                max_steps=600,
                min_steps=100,
                check_every=100,
                convergence_tolerance=1.0e-4,
                consecutive_convergence_checks=2,
            ),
            pinn=PINNConfig(
                hidden_layers=3,
                hidden_width=24,
                interior_pool=1_500,
                interior_batch=256,
                boundary_points=96,
                adam_steps=20,
                lbfgs_steps=0,
                log_every=5,
                balance_every=5,
                checkpoint_every=10,
                supervised_points=1_000,
                evaluation_batch=2_048,
            ),
            output_dir=output_dir,
        )

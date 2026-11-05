"""Typed loading and validation for the authoritative project configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Geometry:
    base_width_m: float
    extrusion_depth_m: float
    base_thickness_m: float
    chip_width_m: float
    candidate_fins: int
    fin_thickness_m: float
    fin_height_bounds_m: tuple[float, float]
    density_bounds: tuple[float, float]
    base_elements_x: int
    base_elements_z: int
    fin_elements: int


@dataclass(frozen=True)
class Material:
    name: str
    conductivity_w_mk: float
    density_kg_m3: float
    emissivity: float


@dataclass(frozen=True)
class LoadCase:
    name: str
    power_w: float
    ambient_k: float
    chip_limit_k: float


@dataclass(frozen=True)
class ProjectConfig:
    raw: dict[str, Any]
    geometry: Geometry
    material: Material
    load_cases: tuple[LoadCase, ...]


def _pair(values: list[float], label: str) -> tuple[float, float]:
    if len(values) != 2 or values[0] >= values[1]:
        raise ValueError(f"{label} must contain increasing [lower, upper] values")
    return float(values[0]), float(values[1])


def load_config(path: str | Path) -> ProjectConfig:
    """Load YAML and enforce invariants that affect the FE topology."""

    source = Path(path)
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if raw.get("schema_version") != 1:
        raise ValueError("Unsupported config schema_version")
    g = raw["geometry"]
    geometry = Geometry(
        base_width_m=float(g["base_width_m"]),
        extrusion_depth_m=float(g["extrusion_depth_m"]),
        base_thickness_m=float(g["base_thickness_m"]),
        chip_width_m=float(g["chip_width_m"]),
        candidate_fins=int(g["candidate_fins"]),
        fin_thickness_m=float(g["fin_thickness_m"]),
        fin_height_bounds_m=_pair(g["fin_height_bounds_m"], "fin_height_bounds_m"),
        density_bounds=_pair(g["density_bounds"], "density_bounds"),
        base_elements_x=int(g["base_elements_x"]),
        base_elements_z=int(g["base_elements_z"]),
        fin_elements=int(g["fin_elements"]),
    )
    if geometry.base_elements_x % geometry.candidate_fins:
        raise ValueError("base_elements_x must be divisible by candidate_fins")
    if geometry.chip_width_m > geometry.base_width_m:
        raise ValueError("chip width cannot exceed the base width")
    m = raw["material"]
    material = Material(str(m["name"]), float(m["conductivity_w_mk"]), float(m["density_kg_m3"]), float(m["emissivity"]))
    if not 0.0 <= material.emissivity <= 1.0:
        raise ValueError("emissivity must be in [0, 1]")
    cases = tuple(LoadCase(name=name, **{key: float(value) for key, value in data.items()}) for name, data in raw["load_cases"].items())
    if len(cases) < 2:
        raise ValueError("At least two PDE response constraints are required")
    return ProjectConfig(raw=raw, geometry=geometry, material=material, load_cases=cases)

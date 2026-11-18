"""Typed loading and validation for the authoritative project configuration."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
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
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError(f"{label} must contain increasing [lower, upper] values")
    pair = float(values[0]), float(values[1])
    if not all(isfinite(value) for value in pair) or pair[0] >= pair[1]:
        raise ValueError(f"{label} must contain increasing [lower, upper] values")
    return pair


def _positive(value: float, label: str) -> float:
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{label} must be positive and finite")
    return result


def _positive_integer(value: int, label: str) -> int:
    result = int(value)
    if result != value or result <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return result


def load_config(path: str | Path) -> ProjectConfig:
    """Load YAML and enforce invariants that affect the FE topology."""

    source = Path(path)
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Project configuration must contain a YAML mapping")
    if raw.get("schema_version") != 1:
        raise ValueError("Unsupported config schema_version")
    g = raw["geometry"]
    geometry = Geometry(
        base_width_m=_positive(g["base_width_m"], "base_width_m"),
        extrusion_depth_m=_positive(g["extrusion_depth_m"], "extrusion_depth_m"),
        base_thickness_m=_positive(g["base_thickness_m"], "base_thickness_m"),
        chip_width_m=_positive(g["chip_width_m"], "chip_width_m"),
        candidate_fins=_positive_integer(g["candidate_fins"], "candidate_fins"),
        fin_thickness_m=_positive(g["fin_thickness_m"], "fin_thickness_m"),
        fin_height_bounds_m=_pair(g["fin_height_bounds_m"], "fin_height_bounds_m"),
        density_bounds=_pair(g["density_bounds"], "density_bounds"),
        base_elements_x=_positive_integer(g["base_elements_x"], "base_elements_x"),
        base_elements_z=_positive_integer(g["base_elements_z"], "base_elements_z"),
        fin_elements=_positive_integer(g["fin_elements"], "fin_elements"),
    )
    if geometry.fin_height_bounds_m[0] <= 0.0:
        raise ValueError("fin_height_bounds_m must be positive")
    if not 0.0 < geometry.density_bounds[0] < geometry.density_bounds[1] <= 1.0:
        raise ValueError("density_bounds must lie in (0, 1]")
    if geometry.base_elements_x % geometry.candidate_fins:
        raise ValueError("base_elements_x must be divisible by candidate_fins")
    if geometry.chip_width_m > geometry.base_width_m:
        raise ValueError("chip width cannot exceed the base width")
    m = raw["material"]
    material = Material(
        str(m["name"]),
        _positive(m["conductivity_w_mk"], "conductivity_w_mk"),
        _positive(m["density_kg_m3"], "density_kg_m3"),
        float(m["emissivity"]),
    )
    if not 0.0 <= material.emissivity <= 1.0:
        raise ValueError("emissivity must be in [0, 1]")
    cases = tuple(
        LoadCase(
            name=name,
            power_w=_positive(data["power_w"], f"{name}.power_w"),
            ambient_k=_positive(data["ambient_k"], f"{name}.ambient_k"),
            chip_limit_k=_positive(data["chip_limit_k"], f"{name}.chip_limit_k"),
        )
        for name, data in raw["load_cases"].items()
    )
    if len(cases) < 2:
        raise ValueError("At least two PDE response constraints are required")
    if any(case.chip_limit_k <= case.ambient_k for case in cases):
        raise ValueError(
            "Each chip temperature limit must exceed its ambient temperature"
        )
    optimization = raw["optimization"]
    threshold = float(optimization["topology_threshold"])
    if not geometry.density_bounds[0] < threshold < geometry.density_bounds[1]:
        raise ValueError("topology_threshold must lie strictly inside density_bounds")
    _positive(
        optimization["scaled_feasibility_tolerance"],
        "scaled_feasibility_tolerance",
    )
    return ProjectConfig(raw=raw, geometry=geometry, material=material, load_cases=cases)

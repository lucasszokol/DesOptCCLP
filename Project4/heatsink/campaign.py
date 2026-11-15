"""The documented optimization sequence used for final report data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import HeatSinkModel
from .optimize import OptimizationRun, optimize_design


@dataclass(frozen=True)
class CampaignResult:
    linear_fixed: OptimizationRun
    nonlinear_fixed: OptimizationRun
    continuation: tuple[OptimizationRun, ...]
    topology_starts: tuple[OptimizationRun, ...]
    threshold_polish: OptimizationRun
    kkt_polish: OptimizationRun
    binary_density: np.ndarray


def run_campaign(model: HeatSinkModel) -> CampaignResult:
    """Execute linear, N2, topology, threshold, and KKT-polish stages."""

    maximum_height = model.config.geometry.fin_height_bounds_m[1]
    start = model.initial_design(maximum_height)
    linear = optimize_design(
        model,
        start,
        name="linear_fixed_topology",
        fixed_topology=True,
        nonlinear=False,
        penalty=1.0,
    )
    nonlinear = optimize_design(
        model,
        linear.full_design,
        name="nonlinear_fixed_topology",
        fixed_topology=True,
        nonlinear=True,
        penalty=1.0,
    )
    current = nonlinear.full_design.copy()
    stages = []
    for penalty in model.config.raw["optimization"]["simp_penalties"]:
        stage = optimize_design(
            model,
            current,
            name=f"topology_simp_p{float(penalty):g}",
            fixed_topology=False,
            nonlinear=True,
            penalty=float(penalty),
        )
        stages.append(stage)
        current = stage.full_design

    count = model.config.geometry.candidate_fins
    threshold = float(model.config.raw["optimization"]["topology_threshold"])
    density_floor = float(model.config.raw["optimization"]["simp_density_floor"])
    # Challenge the all-solid continuation with two asymmetric starts. These
    # are additional p=3 starts, not independent continuation schedules.
    candidates = [stages[-1]]
    for index, name in ((0, "left_edge"), (count // 2, "interior")):
        trial = model.initial_design(maximum_height)
        trial[count + index] = density_floor
        candidates.append(optimize_design(
            model, trial, name=f"topology_start_{name}", fixed_topology=False,
            nonlinear=True, penalty=float(model.config.raw["optimization"]["simp_penalties"][-1]),
        ))
    tolerance = float(model.config.raw["optimization"]["scaled_feasibility_tolerance"])
    eligible = [run for run in candidates if run.result.success and
                max(r.scaled_constraint for r in run.responses) <= tolerance]
    if not eligible:
        raise RuntimeError("No successful feasible topology start")
    current = min(eligible, key=lambda run: run.mass_kg).full_design
    binary = np.where(current[count:] >= threshold, 1.0, density_floor)
    threshold_start = np.r_[current[:count], binary]
    physical_density = model.split_design(threshold_start)[2]
    if np.any((physical_density > density_floor + 0.05) & (physical_density < 0.95)):
        raise RuntimeError("Thresholded raw topology is not physically binary after filtering; "
                           "a discrete reanalysis is required before publication")
    threshold_polish = optimize_design(
        model,
        threshold_start,
        name="threshold_height_reoptimization",
        fixed_topology=True,
        frozen_density=binary,
        nonlinear=True,
        penalty=3.0,
    )
    kkt = optimize_design(
        model,
        threshold_polish.full_design,
        name="trust_constr_kkt_polish",
        fixed_topology=True,
        frozen_density=binary,
        nonlinear=True,
        penalty=3.0,
        method="trust-constr",
        max_iterations=350,
    )
    return CampaignResult(
        linear_fixed=linear,
        nonlinear_fixed=nonlinear,
        continuation=tuple(stages),
        topology_starts=tuple(candidates),
        threshold_polish=threshold_polish,
        kkt_polish=kkt,
        binary_density=binary,
    )

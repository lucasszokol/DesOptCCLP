"""Canonical JSON serialization shared by the report and Three.js viewer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .model import HeatSinkModel
from .campaign import CampaignResult


def _design_view(model: HeatSinkModel, name: str, design: np.ndarray, nonlinear: bool) -> dict:
    heights, _, density = model.split_design(design)
    cases = []
    nominal_temperature = None
    for case in model.config.load_cases:
        response = model.response_with_adjoint(design, case, nonlinear=nonlinear)
        cases.append(
            {
                "name": case.name,
                "power_w": case.power_w,
                "ambient_k": case.ambient_k,
                "limit_k": case.chip_limit_k,
                "ks_temperature_k": response.ks_temperature_k,
                "scaled_constraint": response.scaled_constraint,
                "passed": response.scaled_constraint <= 0.0,
                "energy_imbalance_w": response.solve.energy_imbalance_w,
                "newton_iterations": response.solve.iterations,
            }
        )
        if nominal_temperature is None:
            nominal_temperature = response.solve.temperature_k
    assert nominal_temperature is not None
    fin_temperatures = []
    for dofs in model.fin_dofs:
        fin_temperatures.append([float(value) for value in nominal_temperature[dofs]])
    return {
        "name": name,
        "mass_kg": model.mass_kg(design),
        "heights_m": heights.tolist(),
        "densities": density.tolist(),
        "base_temperature_k": nominal_temperature[: model.base_dofs].tolist(),
        "fin_temperature_k": fin_temperatures,
        "load_cases": cases,
    }


def preliminary_payload(model: HeatSinkModel) -> dict:
    design = model.initial_design()
    g = model.config.geometry
    return {
        "schema_version": 1,
        "status": "awaiting_human_gate",
        "units": {"length": "m", "temperature": "K", "mass": "kg", "power": "W"},
        "geometry": {
            "base_width_m": g.base_width_m,
            "base_depth_m": g.extrusion_depth_m,
            "base_thickness_m": g.base_thickness_m,
            "fin_thickness_m": g.fin_thickness_m,
            "fin_x_m": model.x[model.fin_x_indices].tolist(),
        },
        "designs": {
            "initial": _design_view(model, "Initial uniform design", design, True),
            "optimized": None,
        },
        "optimization_history": [],
        "verification": {"status": "awaiting_student_derivation", "tests": []},
        "gradient_checks": [],
        "kkt": None,
    }


def final_payload(
    model: HeatSinkModel,
    campaign: CampaignResult,
    verification: dict,
    gradient_checks: list[dict],
    sensitivity_cost: dict,
) -> dict:
    initial = model.initial_design()
    final_run = campaign.kkt_polish
    all_runs = [
        campaign.linear_fixed,
        campaign.nonlinear_fixed,
        *campaign.continuation,
        campaign.threshold_polish,
        campaign.kkt_polish,
    ]
    history = []
    for run in all_runs:
        for design, mass, margins in zip(
            run.history.designs, run.history.mass_kg, run.history.constraint_margins
        ):
            history.append(
                {"stage": run.name, "design": design, "mass_kg": mass, "margins": margins}
            )
    multipliers = getattr(final_run.result, "v", None)
    if multipliers is not None:
        multipliers = [np.asarray(value).tolist() for value in multipliers]
    g = model.config.geometry
    return {
        "schema_version": 1,
        "status": "final",
        "units": {"length": "m", "temperature": "K", "mass": "kg", "power": "W"},
        "geometry": {
            "base_width_m": g.base_width_m,
            "base_depth_m": g.extrusion_depth_m,
            "base_thickness_m": g.base_thickness_m,
            "fin_thickness_m": g.fin_thickness_m,
            "fin_x_m": model.x[model.fin_x_indices].tolist(),
        },
        "designs": {
            "initial": _design_view(model, "Initial uniform design", initial, True),
            "optimized": _design_view(model, "Nonlinear topology optimum", final_run.full_design, True),
            "linear_fixed": _design_view(model, "Linear fixed-topology optimum", campaign.linear_fixed.full_design, False),
            "nonlinear_fixed": _design_view(model, "Nonlinear fixed-topology optimum", campaign.nonlinear_fixed.full_design, True),
        },
        "optimization_history": history,
        "verification": verification,
        "gradient_checks": gradient_checks,
        "sensitivity_cost": sensitivity_cost,
        "kkt": {
            "success": bool(final_run.result.success),
            "message": str(final_run.result.message),
            "optimality": float(getattr(final_run.result, "optimality", np.nan)),
            "constraint_violation": float(getattr(final_run.result, "constr_violation", np.nan)),
            "multipliers": multipliers,
        },
    }


def write_json(payload: dict, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

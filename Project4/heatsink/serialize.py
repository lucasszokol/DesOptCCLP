"""Canonical JSON serialization shared by the report and Three.js viewer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import jsonschema

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
                "chip_peak_temperature_k": float(np.max(response.solve.temperature_k[model.chip_dofs()])),
                "scaled_constraint": response.scaled_constraint,
                "passed": response.scaled_constraint <= float(model.config.raw["optimization"]["scaled_feasibility_tolerance"]),
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
        "model_configuration": model.config.raw,
        "thermal_dofs": model.ndof,
        "units": {"length": "m", "temperature": "K", "mass": "kg", "power": "W"},
        "geometry": {
            "base_width_m": g.base_width_m,
            "base_depth_m": g.extrusion_depth_m,
            "base_thickness_m": g.base_thickness_m,
            "fin_thickness_m": g.fin_thickness_m,
            "base_elements_x": g.base_elements_x,
            "base_elements_z": g.base_elements_z,
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
    if multipliers is None or len(multipliers) < 2:
        raise ValueError("KKT polish did not return constraint and bound multipliers")
    # trust-constr uses lower-bounded positive margins, so its inequality
    # multipliers are nonpositive; bound multipliers are signed by active side.
    margins = -np.array([response.scaled_constraint for response in final_run.responses])
    constraint_complementarity = float(np.max(np.abs(np.asarray(multipliers[0]) * margins)))
    # The optimizer uses (height - lower) / (upper - lower). Its recorded
    # physical-bound complementarity uses the corresponding transformed
    # multipliers and physical slacks, so do not assume height / upper.
    bound_complementarity = float(final_run.result.bound_complementarity_inf_norm)
    return {
        "schema_version": 1,
        "status": "final",
        "model_configuration": model.config.raw,
        "thermal_dofs": model.ndof,
        "units": {"length": "m", "temperature": "K", "mass": "kg", "power": "W"},
        "geometry": {
            "base_width_m": g.base_width_m,
            "base_depth_m": g.extrusion_depth_m,
            "base_thickness_m": g.base_thickness_m,
            "fin_thickness_m": g.fin_thickness_m,
            "base_elements_x": g.base_elements_x,
            "base_elements_z": g.base_elements_z,
            "fin_x_m": model.x[model.fin_x_indices].tolist(),
        },
        "designs": {
            "initial": _design_view(model, "Initial uniform design", initial, True),
            "optimized": _design_view(model, "Nonlinear topology optimum", final_run.full_design, True),
            "linear_fixed": _design_view(model, "Linear fixed-topology optimum", campaign.linear_fixed.full_design, False),
            "nonlinear_fixed": _design_view(model, "Nonlinear fixed-topology optimum", campaign.nonlinear_fixed.full_design, True),
        },
        "optimization_history": history,
        "topology_starts": [
            {"name": run.name, "success": bool(run.result.success),
             "message": str(run.result.message), "mass_kg": run.mass_kg,
             "max_scaled_constraint": max(r.scaled_constraint for r in run.responses),
             "raw_densities": run.full_design[model.config.geometry.candidate_fins:].tolist(),
             "filtered_densities": model.split_design(run.full_design)[2].tolist()}
            for run in campaign.topology_start_runs
        ],
        "verification": verification,
        "gradient_checks": gradient_checks,
        "sensitivity_cost": sensitivity_cost,
        "kkt": {
            "success": bool(final_run.result.success),
            "message": str(final_run.result.message),
            "optimality": float(getattr(final_run.result, "optimality", np.nan)),
            "physical_stationarity_inf_norm": float(final_run.result.physical_stationarity_inf_norm),
            "constraint_violation": float(getattr(final_run.result, "constr_violation", np.nan)),
            "constraint_complementarity": constraint_complementarity,
            "bound_complementarity": bound_complementarity,
            "multipliers": multipliers,
        },
    }


def write_json(payload: dict, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def validate_final_payload(payload: dict, schema_path: Path, tolerance: float, gradient_tolerance: float) -> None:
    """Reject incomplete or infeasible final evidence before publication."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)
    if payload.get("status") != "final":
        raise ValueError("Final publication requires final status")
    g = payload["geometry"]
    count = len(g["fin_x_m"])
    base_count = (g["base_elements_x"] + 1) * (g["base_elements_z"] + 1)
    balance_tolerance = float(payload["model_configuration"]["verification"]["energy_balance_relative_tolerance"])
    designs = [payload["designs"][name] for name in ("initial", "optimized", "linear_fixed", "nonlinear_fixed")]
    designs.append(payload["uncertainty"]["design"])
    for design in [*designs, payload["uncertainty"]["baseline_design"]]:
        if (len(design["heights_m"]) != count or len(design["densities"]) != count or
                len(design["fin_temperature_k"]) != count or len(design["base_temperature_k"]) != base_count):
            raise ValueError(f"Geometry/field dimensions disagree for {design['name']}")
        numerical_fields = (design["mass_kg"], design["heights_m"], design["densities"],
                            design["base_temperature_k"], design["fin_temperature_k"])
        if any(not np.all(np.isfinite(field)) for field in numerical_fields):
            raise ValueError(f"Non-finite geometry or field in {design['name']}")
        for case in design["load_cases"]:
            if (not np.isfinite(case["energy_imbalance_w"]) or
                    abs(case["energy_imbalance_w"]) > balance_tolerance * case["power_w"]):
                raise ValueError(f"Energy balance failed for {design['name']}: {case['name']}")
            if (not np.isfinite(case["chip_peak_temperature_k"]) or
                    case["chip_peak_temperature_k"] > case["ks_temperature_k"] + 1e-10):
                raise ValueError(f"Invalid chip peak for {design['name']}: {case['name']}")
    for design in designs[1:]:
        if any(not np.isfinite(c["scaled_constraint"]) or c["scaled_constraint"] > tolerance or not c["passed"] for c in design["load_cases"]):
            raise ValueError(f"Design {design['name']} is infeasible or non-finite")
    config = payload["model_configuration"]
    nominal_cases = config["load_cases"]
    uncertainty = config["uncertainty"]
    expected_scenarios = {}
    for name, case in nominal_cases.items():
        for sign, suffix in ((-1, "low"), (1, "high")):
            expected_scenarios[f"{name}_{suffix}"] = {
                "power_w": case["power_w"] * (1 + sign * uncertainty["power_fraction"]),
                "ambient_k": case["ambient_k"] + sign * uncertainty["ambient_delta_k"],
                "limit_k": case["chip_limit_k"],
            }
    expected_nominal = {name: {"power_w": case["power_w"], "ambient_k": case["ambient_k"],
                               "limit_k": case["chip_limit_k"]} for name, case in nominal_cases.items()}
    for design, expected in [(item, expected_nominal) for item in designs[:4]] + [
            (payload["uncertainty"]["design"], expected_scenarios),
            (payload["uncertainty"]["baseline_design"], expected_scenarios)]:
        cases = design["load_cases"]
        if len(cases) != len(expected) or {case["name"] for case in cases} != set(expected):
            raise ValueError(f"Load-case coverage does not match configuration for {design['name']}")
        for case in cases:
            if any(not np.isclose(case[key], value, rtol=1e-12, atol=1e-12)
                   for key, value in expected[case["name"]].items()):
                raise ValueError(f"Load-case parameters do not match configuration for {case['name']}")
            scaled = case["ks_temperature_k"] / case["limit_k"] - 1.0
            if not np.isclose(case["scaled_constraint"], scaled, rtol=1e-10, atol=1e-12):
                raise ValueError(f"Constraint value is inconsistent for {case['name']}")
            if case["passed"] != (case["scaled_constraint"] <= tolerance):
                raise ValueError(f"Constraint pass flag is inconsistent for {case['name']}")
    verification_checks = [check for group in payload["verification"]["groups"] for check in group["checks"]]
    if (not verification_checks or any(not check["pass"] for check in verification_checks) or
            payload["verification"]["passed_checks"] != len(verification_checks) or
            payload["verification"]["total_checks"] != len(verification_checks)):
        raise ValueError("Verification check evidence is incomplete or failed")
    fin_check = payload.get("nonlinear_fin_check", {})
    if fin_check.get("status") != "passed" or len(fin_check.get("meshes", [])) != 2:
        raise ValueError("Nonlinear fin cross-check is missing or failed")
    if any(not c.get("pass") for c in payload["gradient_checks"]):
        raise ValueError("Gradient check failed")
    checks = payload["uncertainty"]["gradient_checks"]
    scenarios = {case["name"] for case in payload["uncertainty"]["design"]["load_cases"]}
    baseline_scenarios = {case["name"] for case in payload["uncertainty"]["baseline_design"]["load_cases"]}
    if baseline_scenarios != scenarios:
        raise ValueError("Uncertainty baseline scenarios do not match optimized scenarios")
    coverage = {(c["scenario"], c["variable_family"]) for c in checks}
    if coverage != {(name, family) for name in scenarios for family in ("height", "density")}:
        raise ValueError("Uncertainty gradient coverage is incomplete")
    if any(not np.isfinite(c["relative_error"]) or c["relative_error"] > gradient_tolerance for c in checks):
        raise ValueError("Uncertainty gradient check failed")
    kkt = payload["kkt"]
    residuals = (kkt["optimality"], kkt["constraint_violation"],
                 kkt["constraint_complementarity"], kkt["bound_complementarity"])
    if any(not np.isfinite(value) or value > tolerance for value in residuals):
        raise ValueError("KKT residual exceeds tolerance")

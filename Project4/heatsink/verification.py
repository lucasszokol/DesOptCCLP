"""Student-truth ingestion plus discrete-adjoint verification."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .model import HeatSinkModel


def taylor_checks(model: HeatSinkModel, design: np.ndarray) -> list[dict]:
    """Central differences and second-order Taylor remainders for every case."""

    count = model.config.geometry.candidate_fins
    base_design = np.asarray(design, dtype=float).copy()
    if np.any(base_design[count:] <= 0.2) or np.any(base_design[count:] >= 0.8):
        raise ValueError("Taylor checks require interior density values in (0.2, 0.8)")
    checks: list[dict] = []
    for case_index, case in enumerate(model.config.load_cases):
        response = model.response_with_adjoint(base_design, case, nonlinear=True)
        index = np.arange(count, dtype=float)
        for family, direction in (
            (
                "height",
                np.r_[np.linspace(0.001, 0.004, count) * (1.0 + 0.12 * np.sin(index)), np.zeros(count)],
            ),
            (
                "density",
                np.r_[np.zeros(count), -np.linspace(0.05, 0.20, count) * (1.0 + 0.10 * np.cos(index))],
            ),
        ):
            derivative = float(response.gradient @ direction)
            rows = []
            for step in np.logspace(0, -5, 11):
                plus = model.response_with_adjoint(base_design + step * direction, case, nonlinear=True)
                minus = model.response_with_adjoint(base_design - step * direction, case, nonlinear=True)
                central = (plus.scaled_constraint - minus.scaled_constraint) / (2.0 * step)
                derivative_error = abs(float(central) - derivative)
                relative_derivative_error = derivative_error / max(abs(derivative), 1.0e-15)
                remainder = abs(plus.scaled_constraint - response.scaled_constraint - step * derivative)
                rows.append(
                    {
                        "step": float(step),
                        "central_derivative": float(central),
                        "adjoint_derivative": derivative,
                        "derivative_absolute_error": derivative_error,
                        "derivative_relative_error": relative_derivative_error,
                        "absolute_error": float(remainder),
                    }
                )
            # The largest four steps expose the asymptotic O(h^2) remainder;
            # smaller steps are retained to show the eventual roundoff floor.
            slope = float(
                np.polyfit(
                    np.log([row["step"] for row in rows[:4]]),
                    np.log([row["absolute_error"] for row in rows[:4]]),
                    1,
                )[0]
            )
            checks.append(
                {
                    "load_case": case.name,
                    "variable_family": family,
                    "taylor_slope": slope,
                    "minimum_relative_directional_error": min(
                        row["derivative_relative_error"] for row in rows
                    ),
                    "rows": rows,
                }
            )
            checks[-1]["pass"] = bool(
                model.config.raw["verification"]["taylor_slope_bounds"][0]
                <= slope
                <= model.config.raw["verification"]["taylor_slope_bounds"][1]
                and checks[-1]["minimum_relative_directional_error"]
                <= float(model.config.raw["verification"]["gradient_relative_tolerance"])
            )
    return checks


def objective_gradient_checks(model: HeatSinkModel, design: np.ndarray) -> list[dict]:
    """Check both mass-objective variable families independently."""

    count = model.config.geometry.candidate_fins
    gradient = model.mass_gradient(design)
    rows = []
    for family, direction in (
        ("height", np.r_[np.linspace(0.001, 0.004, count), np.zeros(count)]),
        ("density", np.r_[np.zeros(count), np.linspace(-0.05, -0.20, count)]),
    ):
        step = 1.0e-5
        central = (
            model.mass_kg(design + step * direction)
            - model.mass_kg(design - step * direction)
        ) / (2.0 * step)
        analytic = float(gradient @ direction)
        relative = abs(central - analytic) / max(abs(analytic), 1.0e-15)
        rows.append(
            {
                "objective": "mass_kg",
                "variable_family": family,
                "central_derivative": float(central),
                "analytic_derivative": analytic,
                "relative_error": float(relative),
                "pass": bool(
                    relative
                    <= float(model.config.raw["verification"]["gradient_relative_tolerance"])
                ),
            }
        )
    return rows


def sensitivity_cost_comparison(model: HeatSinkModel, design: np.ndarray) -> dict:
    """Measure one all-variable adjoint against a central-difference estimate."""

    case = model.config.load_cases[0]
    start = perf_counter()
    response = model.response_with_adjoint(design, case, nonlinear=True)
    adjoint_seconds = perf_counter() - start
    start = perf_counter()
    step = 1.0e-5
    finite = np.zeros(design.size)
    for index in range(design.size):
        perturbation = np.zeros(design.size)
        perturbation[index] = step
        plus = model.response_with_adjoint(design + perturbation, case, nonlinear=True)
        minus = model.response_with_adjoint(design - perturbation, case, nonlinear=True)
        finite[index] = (plus.scaled_constraint - minus.scaled_constraint) / (2.0 * step)
    finite_seconds = perf_counter() - start
    relative_error = np.linalg.norm(finite - response.gradient) / max(np.linalg.norm(finite), 1.0e-15)
    return {
        "design_variables": int(design.size),
        "adjoint_seconds": adjoint_seconds,
        "finite_difference_seconds": finite_seconds,
        "speedup": finite_seconds / adjoint_seconds,
        "relative_gradient_error": float(relative_error),
        "adjoint_linear_solves_per_response": 1,
        "central_difference_state_solves": int(2 * design.size),
    }


def student_truth_summary(truth: dict) -> dict:
    """Preserve the submitted truth and attestation without recomputing it."""

    return {
        "status": truth["status"],
        "student_attestation": truth["student_attestation"],
        "benchmarks": {key: truth[key] for key in ("v1", "v2", "v3", "v6")},
    }


def write_sensitivity_evidence(
    checks: list[dict], objective_checks: list[dict], cost: dict, directory: Path
) -> dict:
    """Write the reproducible V7 payload without manual result transcription."""

    directory.mkdir(parents=True, exist_ok=True)
    passed = (
        all(check["pass"] for check in checks)
        and all(check["pass"] for check in objective_checks)
        and cost["relative_gradient_error"] <= 1.0e-5
    )
    payload = {
        "id": "V7", "status": "passed" if passed else "failed",
        "constraint_checks": checks, "objective_checks": objective_checks,
        "cost_comparison": cost,
    }
    (directory / "sensitivity.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# V7 adjoint and sensitivity evidence", "",
        f"Status: **{payload['status'].upper()}**", "",
        "| Response | Variable family | Taylor slope | Best relative directional error | Pass |",
        "|---|---|---:|---:|:---:|",
    ]
    lines.extend(
        f"| {check['load_case']} constraint | {check['variable_family']} | "
        f"{check['taylor_slope']:.6g} | {check['minimum_relative_directional_error']:.3g} | "
        f"{'PASS' if check['pass'] else 'FAIL'} |"
        for check in checks
    )
    lines.extend(["", "| Objective | Variable family | Relative error | Pass |", "|---|---|---:|:---:|"])
    lines.extend(
        f"| mass | {check['variable_family']} | {check['relative_error']:.3g} | "
        f"{'PASS' if check['pass'] else 'FAIL'} |"
        for check in objective_checks
    )
    lines.extend(
        [
            "", f"Adjoint/finite-difference relative gradient error: `{cost['relative_gradient_error']:.6g}`.",
            f"Measured speedup: `{cost['speedup']:.3g}x` ({cost['central_difference_state_solves']} central-difference state solves).",
        ]
    )
    (directory / "sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload

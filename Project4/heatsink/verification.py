"""Agent-independent truth ingestion plus adjoint Taylor checks."""

from __future__ import annotations

from time import perf_counter

import numpy as np

from .model import HeatSinkModel


def taylor_checks(model: HeatSinkModel, design: np.ndarray) -> list[dict]:
    """Central-difference sweeps for every case and variable family."""

    count = model.config.geometry.candidate_fins
    checks: list[dict] = []
    for case_index, case in enumerate(model.config.load_cases):
        response = model.response_with_adjoint(design, case, nonlinear=True)
        for family, direction in (
            ("height", np.r_[np.linspace(-0.004, 0.004, count), np.zeros(count)]),
            ("density", np.r_[np.zeros(count), np.linspace(-0.08, 0.08, count)]),
        ):
            derivative = float(response.gradient @ direction)
            rows = []
            for step in np.logspace(-1, -5, 9):
                plus = model.response_with_adjoint(design + step * direction, case, nonlinear=True)
                minus = model.response_with_adjoint(design - step * direction, case, nonlinear=True)
                central = (plus.scaled_constraint - minus.scaled_constraint) / (2.0 * step)
                rows.append(
                    {
                        "step": float(step),
                        "central_derivative": float(central),
                        "adjoint_derivative": derivative,
                        "absolute_error": abs(float(central) - derivative),
                    }
                )
            errors = np.array([row["absolute_error"] for row in rows])
            steps = np.array([row["step"] for row in rows])
            usable = (errors > 1.0e-13) & (errors < 1.0e-3)
            slope = float(np.polyfit(np.log(steps[usable]), np.log(errors[usable]), 1)[0]) if usable.sum() >= 2 else float("nan")
            checks.append(
                {
                    "load_case": case.name,
                    "variable_family": family,
                    "taylor_slope": slope,
                    "rows": rows,
                }
            )
    return checks


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

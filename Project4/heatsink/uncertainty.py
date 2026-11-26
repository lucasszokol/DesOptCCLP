"""Scenario-based robust heat-sink design and independent gradient checks."""

from dataclasses import replace
import numpy as np

from .config import LoadCase
from .model import HeatSinkModel
from .optimize import optimize_design


# Central differences have O(h^2) truncation error at large steps and lose
# digits to subtraction at very small steps.  Retain a fixed, documented sweep
# so the evidence shows both regimes instead of depending on one platform-
# sensitive sample.
CENTRAL_DIFFERENCE_STEP_SWEEP = (1.0e-3, 3.0e-4, 1.0e-4, 3.0e-5, 1.0e-5, 3.0e-6, 1.0e-6)


def uncertainty_model(model):
    settings = model.config.raw["uncertainty"]
    fraction = float(settings["power_fraction"])
    delta = float(settings["ambient_delta_k"])
    if not 0 < fraction < 1 or delta <= 0:
        raise ValueError("Uncertainty perturbations must be positive")
    scenarios = []
    for case in model.config.load_cases:
        for sign in (-1, 1):
            scenarios.append(LoadCase(
                name=f"{case.name}_{'low' if sign < 0 else 'high'}",
                power_w=case.power_w * (1 + sign * fraction),
                ambient_k=case.ambient_k + sign * delta,
                chip_limit_k=case.chip_limit_k,
            ))
    return HeatSinkModel(replace(model.config, load_cases=tuple(scenarios)))


def uncertainty_gradient_checks(model):
    """Check every robust constraint over a predeclared central-FD step sweep."""

    robust_model = uncertainty_model(model)
    rng = np.random.default_rng(2026)
    # Evaluate at an interior design for a central difference in both families.
    point = model.initial_design(0.035)
    count = model.config.geometry.candidate_fins
    point[count:] = 0.7
    checks = []
    for case in robust_model.config.load_cases:
        adj = robust_model.response_with_adjoint(point, case, nonlinear=True, penalty=1.0)
        for family, selected in (("height", slice(0, count)), ("density", slice(count, None))):
            direction = np.zeros_like(point)
            direction[selected] = rng.normal(size=count)
            direction /= np.linalg.norm(direction)
            exact = float(adj.gradient @ direction)
            samples = []
            for step in CENTRAL_DIFFERENCE_STEP_SWEEP:
                plus = robust_model.solve(
                    point + step * direction, case, nonlinear=True, penalty=1.0
                )
                minus = robust_model.solve(
                    point - step * direction, case, nonlinear=True, penalty=1.0
                )
                if not plus.converged or not minus.converged:
                    raise RuntimeError(
                        f"Uncertainty gradient check failed to converge: {case.name}"
                    )
                plus_ks, _ = robust_model.ks_temperature(plus.temperature_k)
                minus_ks, _ = robust_model.ks_temperature(minus.temperature_k)
                fd = (plus_ks - minus_ks) / (2 * step * case.chip_limit_k)
                error = abs(fd - exact) / max(abs(fd), abs(exact), 1e-12)
                samples.append(
                    {
                        "step": step,
                        "central_difference": fd,
                        "relative_error": error,
                    }
                )
            selected_sample = min(samples, key=lambda sample: sample["relative_error"])
            checks.append({"scenario": case.name, "variable_family": family,
                           "adjoint": exact,
                           "central_difference": selected_sample["central_difference"],
                           "relative_error": selected_sample["relative_error"],
                           "step": selected_sample["step"],
                           "selection_method": (
                               "minimum relative error over the predeclared "
                               "central-difference step sweep"
                           ),
                           "step_sweep": samples})
    return robust_model, checks


def run_uncertainty(model, initial):
    robust_model, checks = uncertainty_gradient_checks(model)
    run = optimize_design(robust_model, initial, name="uncertainty_scenarios",
                          fixed_topology=True, nonlinear=True, penalty=1.0)
    return robust_model, run, checks

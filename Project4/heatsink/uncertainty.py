"""Scenario-based robust heat-sink design and independent gradient checks."""

from dataclasses import replace
import numpy as np

from .config import LoadCase
from .model import HeatSinkModel
from .optimize import optimize_design


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


def run_uncertainty(model, initial):
    robust_model = uncertainty_model(model)
    run = optimize_design(robust_model, initial, name="uncertainty_scenarios",
                          fixed_topology=True, nonlinear=True, penalty=1.0)
    rng = np.random.default_rng(2026)
    # Evaluate at an interior design for a central difference in both families.
    point = model.initial_design(0.035)
    count = model.config.geometry.candidate_fins
    point[count:] = 0.7
    step = 1e-6
    checks = []
    for case in robust_model.config.load_cases:
        adj = robust_model.response_with_adjoint(point, case, nonlinear=True, penalty=1.0)
        for family, selected in (("height", slice(0, count)), ("density", slice(count, None))):
            direction = np.zeros_like(point)
            direction[selected] = rng.normal(size=count)
            direction /= np.linalg.norm(direction)
            plus = robust_model.solve(point + step * direction, case, nonlinear=True, penalty=1.0)
            minus = robust_model.solve(point - step * direction, case, nonlinear=True, penalty=1.0)
            if not plus.converged or not minus.converged:
                raise RuntimeError(f"Uncertainty gradient check failed to converge: {case.name}")
            plus_ks, _ = robust_model.ks_temperature(plus.temperature_k)
            minus_ks, _ = robust_model.ks_temperature(minus.temperature_k)
            fd = (plus_ks - minus_ks) / (2 * step * case.chip_limit_k)
            exact = float(adj.gradient @ direction)
            error = abs(fd - exact) / max(abs(fd), abs(exact), 1e-12)
            checks.append({"scenario": case.name, "variable_family": family,
                           "adjoint": exact, "central_difference": fd,
                           "relative_error": error, "step": step})
    return robust_model, run, checks

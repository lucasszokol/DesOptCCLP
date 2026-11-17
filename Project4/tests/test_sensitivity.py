from pathlib import Path

import numpy as np
import pytest

from heatsink.config import load_config
from heatsink.model import HeatSinkModel
from heatsink.verification import (
    objective_gradient_checks,
    sensitivity_cost_comparison,
    taylor_checks,
    ks_state_checks,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("nonlinear", [False, True])
def test_v7_adjoint_directional_and_taylor_checks(nonlinear) -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    count = config.geometry.candidate_fins
    design = np.r_[np.linspace(0.025, 0.040, count), np.linspace(0.45, 0.65, count)]
    checks = taylor_checks(model, design, nonlinear=nonlinear)
    assert len(checks) == 12
    assert {item["direction_name"] for item in checks} == {"structured", "random_0", "random_1"}
    assert {(item["load_case"], item["variable_family"]) for item in checks} == {
        ("nominal", "height"), ("nominal", "density"),
        ("overload", "height"), ("overload", "density"),
    }
    for item in checks:
        assert 1.8 <= item["taylor_slope"] <= 2.2, item
        assert item["minimum_relative_directional_error"] <= 1.0e-5, item
        assert item["pass"]


def test_v7_mass_objective_checks_both_variable_families() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design(0.030)
    design[config.geometry.candidate_fins:] = 0.60
    checks = objective_gradient_checks(model, design)
    assert {check["variable_family"] for check in checks} == {"height", "density"}
    assert all(check["pass"] for check in checks)


def test_v7_all_variable_cost_comparison(monkeypatch) -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design(0.030)
    design[config.geometry.candidate_fins:] = 0.60
    calls = []
    original = model.response_with_adjoint
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(model, "response_with_adjoint", counted)
    evidence = sensitivity_cost_comparison(model, design)
    assert len(calls) == 2  # One warm-up and one timed adjoint; none in FD.
    assert evidence["finite_difference_adjoint_solves"] == 0
    assert evidence["relative_gradient_error"] <= 1.0e-5
    assert evidence["central_difference_state_solves"] == 2 * design.size


def test_ks_derivative_at_ties_nonuniform_states_and_large_offsets() -> None:
    model = HeatSinkModel(load_config(ROOT / "Project4" / "config.yaml"))
    checks = ks_state_checks(model)
    assert len(checks) == 3
    assert all(row["pass"] for row in checks), checks


def test_ks_check_detects_corrupt_state_gradient(monkeypatch) -> None:
    model = HeatSinkModel(load_config(ROOT / "Project4" / "config.yaml"))
    original = model.ks_temperature
    def corrupted(state):
        value, gradient = original(state)
        return value, 1.1 * gradient
    monkeypatch.setattr(model, "ks_temperature", corrupted)
    assert not any(row["pass"] for row in ks_state_checks(model))

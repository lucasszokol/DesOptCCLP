from pathlib import Path

from heatsink.config import load_config
from heatsink.model import HeatSinkModel
from heatsink.verification import (
    objective_gradient_checks,
    sensitivity_cost_comparison,
    taylor_checks,
)


ROOT = Path(__file__).resolve().parents[2]


def test_v7_adjoint_directional_and_taylor_checks() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design(0.030)
    design[config.geometry.candidate_fins:] = 0.60
    checks = taylor_checks(model, design)
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


def test_v7_all_variable_cost_comparison() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design(0.030)
    design[config.geometry.candidate_fins:] = 0.60
    evidence = sensitivity_cost_comparison(model, design)
    assert evidence["relative_gradient_error"] <= 1.0e-5
    assert evidence["central_difference_state_solves"] == 2 * design.size

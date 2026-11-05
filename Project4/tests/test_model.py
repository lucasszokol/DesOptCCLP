from pathlib import Path

import numpy as np

from heatsink.config import load_config
from heatsink.model import HeatSinkModel


ROOT = Path(__file__).resolve().parents[2]


def test_linear_and_nonlinear_models_converge_and_balance_energy() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design()
    case = config.load_cases[0]
    for nonlinear in (False, True):
        result = model.solve(design, case, nonlinear=nonlinear)
        assert result.converged
        assert np.isfinite(result.temperature_k).all()
        assert result.temperature_k.max() > case.ambient_k
        assert abs(result.energy_imbalance_w) / case.power_w < 1.0e-8


def test_model_reflection_symmetry() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design()
    result = model.solve(design, config.load_cases[0], nonlinear=True)
    base = result.temperature_k[: model.base_dofs].reshape(model.nz + 1, model.nx + 1)
    np.testing.assert_allclose(base, base[:, ::-1], rtol=1.0e-10, atol=1.0e-9)


def test_mass_gradient_matches_central_difference() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design()
    direction = np.linspace(-0.3, 0.4, design.size)
    step = 1.0e-6
    finite_difference = (
        model.mass_kg(design + step * direction)
        - model.mass_kg(design - step * direction)
    ) / (2.0 * step)
    adjoint = model.mass_gradient(design) @ direction
    np.testing.assert_allclose(adjoint, finite_difference, rtol=1.0e-8)


def test_nonlinear_adjoint_matches_directional_difference() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    design = model.initial_design()
    direction = np.r_[np.linspace(-0.004, 0.004, 20), np.linspace(-0.08, 0.08, 20)]
    response = model.response_with_adjoint(design, config.load_cases[0], nonlinear=True)
    step = 1.0e-4
    plus = model.response_with_adjoint(design + step * direction, config.load_cases[0], nonlinear=True)
    minus = model.response_with_adjoint(design - step * direction, config.load_cases[0], nonlinear=True)
    finite_difference = (plus.scaled_constraint - minus.scaled_constraint) / (2.0 * step)
    adjoint = response.gradient @ direction
    np.testing.assert_allclose(adjoint, finite_difference, rtol=1.0e-5, atol=1.0e-9)


def test_design_space_contains_a_feasible_bounding_design() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    maximum_material = model.initial_design(config.geometry.fin_height_bounds_m[1])
    responses = [model.response_with_adjoint(maximum_material, case) for case in config.load_cases]
    assert all(response.scaled_constraint <= 0.0 for response in responses)

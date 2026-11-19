from pathlib import Path

import numpy as np
from dataclasses import replace
from scipy.integrate import quad
from scipy.sparse import issparse

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


def test_exact_chip_footprint_and_sparse_tangent() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    weights = model.chip_load_weights()
    half = config.geometry.chip_width_m / 2
    dx = model.x[1] - model.x[0]
    reference = np.array([quad(lambda x: max(0.0, 1.0 - abs(x-node)/dx) / (2*half),
                               -half, half, points=model.x[(model.x > -half) & (model.x < half)])[0]
                          for node in model.x])
    np.testing.assert_allclose(weights[:model.nx+1], reference, rtol=0, atol=1e-12)
    np.testing.assert_allclose(weights.sum(), 1.0, atol=1e-13)
    _, tangent, _ = model.assemble(np.full(model.ndof, 330.0), model.initial_design(),
                                   config.load_cases[0], nonlinear=True, penalty=3.0)
    assert issparse(model.base_matrix) and issparse(tangent)


def test_ks_fixed_physical_points_are_mesh_independent_for_same_field() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    coarse = HeatSinkModel(config)
    fine = HeatSinkModel(replace(config, geometry=replace(config.geometry, base_elements_x=80, base_elements_z=8)))
    coarse_t = np.full(coarse.ndof, 320.0)
    coarse_t[:coarse.nx+1] = 330.0 + 30.0 * (1.0 - np.abs(coarse.x) / .03)
    fine_t = np.full(fine.ndof, 320.0)
    fine_t[:fine.nx+1] = np.interp(fine.x, coarse.x, coarse_t[:coarse.nx+1])
    assert coarse.chip_sampling_matrix().shape[0] == fine.chip_sampling_matrix().shape[0] == 15
    np.testing.assert_allclose(coarse.ks_temperature(coarse_t)[0], fine.ks_temperature(fine_t)[0], rtol=0, atol=1e-11)
    assert coarse.ks_temperature(coarse_t)[0] >= coarse.chip_peak_temperature(coarse_t)

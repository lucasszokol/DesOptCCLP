import json
from pathlib import Path

import numpy as np

from heatsink.config import load_config
from heatsink.model import HeatSinkModel
from heatsink.optimize import OptimizationProblem, optimize_design


ROOT = Path(__file__).resolve().parents[2]


def test_optimizer_interface_shapes_and_gradients() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    full = model.initial_design()
    fixed = OptimizationProblem(model, fixed_topology=True, nonlinear=True, penalty=3.0)
    assert fixed.objective_gradient(full[:20]).shape == (20,)
    assert fixed.margins(full[:20]).shape == (2,)
    assert fixed.margins_jacobian(full[:20]).shape == (2, 20)
    topology = OptimizationProblem(model, fixed_topology=False, nonlinear=True, penalty=3.0)
    assert topology.objective_gradient(full).shape == (40,)
    np.testing.assert_allclose(topology.full_design(full), full)


def test_nonlinear_fixed_run_records_history_and_acceptance() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    run = optimize_design(
        model,
        model.initial_design(config.geometry.fin_height_bounds_m[1]),
        name="test_nonlinear_fixed",
        fixed_topology=True,
        nonlinear=True,
        penalty=1.0,
        max_iterations=100,
    )
    assert run.result.success
    assert run.accepted
    assert run.max_scaled_constraint <= run.feasibility_tolerance
    assert run.elapsed_seconds > 0.0
    lengths = {
        len(run.history.designs),
        len(run.history.mass_kg),
        len(run.history.constraint_margins),
        len(run.history.elapsed_seconds),
    }
    assert len(lengths) == 1
    assert next(iter(lengths)) >= 2
    assert np.all(np.diff(run.history.elapsed_seconds) >= 0.0)


def test_scaled_trust_constr_returns_feasible_kkt_evidence() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    count = config.geometry.candidate_fins
    lower, upper = config.geometry.fin_height_bounds_m
    start_height = upper - 0.0125 * (upper - lower)
    start = np.r_[np.full(count, start_height), np.ones(count)]
    run = optimize_design(
        model,
        start,
        name="test_kkt_polish",
        fixed_topology=True,
        frozen_density=np.ones(count),
        nonlinear=True,
        penalty=3.0,
        method="trust-constr",
        max_iterations=250,
    )
    assert run.result.success
    assert run.accepted
    assert run.result.status == 1
    assert run.result.physical_stationarity_inf_norm < 1.0e-6
    assert run.result.constraint_complementarity_inf_norm < 1.0e-6
    assert run.result.bound_complementarity_inf_norm < 1.0e-6
    assert run.result.constr_violation <= run.feasibility_tolerance
    multipliers = -np.asarray(run.result.constraint_multipliers)
    assert multipliers.shape == (2,)
    assert multipliers[1] > multipliers[0]


def test_generated_campaign_evidence_meets_agent3_contract() -> None:
    path = ROOT / "Project4" / "results" / "optimization" / "campaign.json"
    assert path.exists(), "run python -m Project4.heatsink.campaign first"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    assert evidence["status"] == "complete_with_authoritative_model_blockers"
    assert evidence["comparisons"]["linear_reference_feasible"]
    assert evidence["topology"]["intermediate_count_0p01_0p99"] == 0
    assert evidence["topology"]["threshold_filtered_intermediate_count_0p01_0p99"] == 0
    assert not evidence["topology"]["topology_bonus_demonstrated"]
    screen = evidence["topology"]["single_fin_removal_screen"]
    assert evidence["topology"]["any_single_fin_removal_feasible"] == any(
        row["max_scaled_constraint"] <= evidence["feasibility_tolerance"] for row in screen
    )
    assert len(evidence["topology"]["single_fin_removal_screen"]) == 20
    assert evidence["topology"]["active_fins_after_threshold"] <= evidence["topology"]["candidate_fins"]
    assert len(evidence["starting_points"]["fixed_topology"]) >= 3
    assert len(evidence["starting_points"]["topology"]) >= 3
    final_roles = {
        "simp_continuation",
        "threshold_height_reoptimization",
        "kkt_polish",
    }
    final_runs = [run for run in evidence["runs"] if run["role"] in final_roles]
    assert final_runs
    assert all(run["accepted"] for run in final_runs)
    assert all(
        run["max_scaled_constraint"] <= evidence["feasibility_tolerance"]
        for run in final_runs
    )
    assert evidence["kkt"]["active_constraints"]
    assert evidence["kkt"]["stationarity_inf_norm_physical"] < 1.0e-6
    assert evidence["kkt"]["constraint_complementarity_inf_norm"] < 1.0e-6
    assert evidence["kkt"]["bound_complementarity_inf_norm"] < 1.0e-6

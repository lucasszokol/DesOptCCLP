"""Staged optimization campaign and reproducible Agent 3 evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable

import numpy as np

from .config import load_config
from .gates import HumanGateError, require_human_approvals
from .model import HeatSinkModel
from .optimize import OptimizationRun, optimize_design
from .topology import (
    grayness,
    intermediate_density_count,
    threshold_density,
)


ProgressCallback = Callable[[OptimizationRun], None]


@dataclass(frozen=True)
class CampaignResult:
    linear_fixed: OptimizationRun
    fixed_start_runs: tuple[OptimizationRun, ...]
    nonlinear_fixed: OptimizationRun
    topology_start_runs: tuple[OptimizationRun, ...]
    continuation: tuple[OptimizationRun, ...]
    threshold_polish: OptimizationRun
    kkt_polish: OptimizationRun
    binary_density: np.ndarray
    kkt_seed_label: str
    elapsed_seconds: float


def _run(
    model: HeatSinkModel,
    progress: ProgressCallback | None,
    **kwargs: object,
) -> OptimizationRun:
    result = optimize_design(model, **kwargs)
    if progress is not None:
        progress(result)
    return result


def _select_best(runs: list[OptimizationRun]) -> OptimizationRun:
    accepted = [run for run in runs if run.accepted]
    if not accepted:
        summary = "; ".join(
            f"{run.name}: success={run.result.success}, "
            f"max_g={run.max_scaled_constraint:.6g}"
            for run in runs
        )
        raise RuntimeError(f"no accepted optimization start: {summary}")
    best = accepted[0]
    for run in accepted[1:]:
        if run.mass_kg < best.mass_kg - 1.0e-9:
            best = run
    return best


def _fixed_topology_starts(model: HeatSinkModel) -> list[tuple[str, np.ndarray]]:
    count = model.config.geometry.candidate_fins
    lower, upper = model.config.geometry.fin_height_bounds_m
    span = upper - lower
    position = np.linspace(-1.0, 1.0, count)
    return [
        ("uniform_max", np.r_[np.full(count, upper), np.ones(count)]),
        (
            "uniform_75_percent",
            np.r_[np.full(count, lower + 0.75 * span), np.ones(count)],
        ),
        (
            "symmetric_taper",
            np.r_[upper - 0.25 * span * np.abs(position), np.ones(count)],
        ),
    ]


def _topology_starts(
    model: HeatSinkModel,
    nonlinear_fixed: OptimizationRun,
) -> list[tuple[str, np.ndarray]]:
    count = model.config.geometry.candidate_fins
    upper = model.config.geometry.fin_height_bounds_m[1]
    position = np.linspace(-1.0, 1.0, count)
    return [
        ("from_fixed_topology", nonlinear_fixed.full_design.copy()),
        (
            "uniform_density_0p60",
            np.r_[np.full(count, upper), np.full(count, 0.60)],
        ),
        (
            "edge_weighted_density",
            np.r_[
                np.full(count, upper),
                0.55 + 0.45 * np.abs(position),
            ],
        ),
    ]


def _strictly_feasible_kkt_seed(
    model: HeatSinkModel,
    binary_density: np.ndarray,
    fallback: np.ndarray,
    penalty: float,
) -> tuple[np.ndarray, str]:
    """Find a strictly interior feasible height vector for trust-constr."""

    count = model.config.geometry.candidate_fins
    lower, upper = model.config.geometry.fin_height_bounds_m
    span = upper - lower
    for fraction in (0.05, 0.025, 0.0125, 0.005, 0.0025, 0.001):
        height = upper - fraction * span
        candidate = np.r_[np.full(count, height), binary_density]
        maximum_constraint = max(
            model.response_with_adjoint(
                candidate,
                case,
                nonlinear=True,
                penalty=penalty,
            ).scaled_constraint
            for case in model.config.load_cases
        )
        if maximum_constraint < -1.0e-8:
            return candidate, f"uniform_{fraction:g}_span_below_upper"
    return np.asarray(fallback, dtype=float).copy(), "threshold_polish_fallback"


def run_campaign(
    model: HeatSinkModel,
    *,
    progress: ProgressCallback | None = None,
) -> CampaignResult:
    """Execute multi-start fixed, N2, topology, threshold, and KKT stages."""

    started_at = perf_counter()
    penalties = tuple(
        float(value) for value in model.config.raw["optimization"]["simp_penalties"]
    )
    if not penalties or penalties[0] != 1.0:
        raise ValueError("SIMP continuation must begin at penalty 1")

    maximum_height = model.config.geometry.fin_height_bounds_m[1]
    maximum_design = model.initial_design(maximum_height)
    linear = _run(
        model,
        progress,
        initial_full_design=maximum_design,
        name="linear_fixed_topology",
        fixed_topology=True,
        nonlinear=False,
        penalty=1.0,
    )

    fixed_runs = [
        _run(
            model,
            progress,
            initial_full_design=design,
            name=f"nonlinear_fixed_{label}",
            fixed_topology=True,
            nonlinear=True,
            penalty=1.0,
        )
        for label, design in _fixed_topology_starts(model)
    ]
    nonlinear = _select_best(fixed_runs)

    topology_runs = [
        _run(
            model,
            progress,
            initial_full_design=design,
            name=f"topology_start_{label}_p{penalties[0]:g}",
            fixed_topology=False,
            nonlinear=True,
            penalty=penalties[0],
        )
        for label, design in _topology_starts(model, nonlinear)
    ]
    selected_topology = _select_best(topology_runs)
    continuation = [selected_topology]
    current = selected_topology.full_design
    for penalty in penalties[1:]:
        stage = _run(
            model,
            progress,
            initial_full_design=current,
            name=f"topology_simp_p{penalty:g}",
            fixed_topology=False,
            nonlinear=True,
            penalty=penalty,
        )
        continuation.append(stage)
        if not stage.accepted:
            raise RuntimeError(
                f"SIMP stage {stage.name} was not accepted: "
                f"success={stage.result.success}, max_g={stage.max_scaled_constraint:.6g}"
            )
        current = stage.full_design

    count = model.config.geometry.candidate_fins
    threshold = float(model.config.raw["optimization"]["topology_threshold"])
    density_floor = float(model.config.raw["optimization"]["simp_density_floor"])
    binary = threshold_density(current[count:], threshold, density_floor)
    threshold_start = np.r_[current[:count], binary]
    final_penalty = penalties[-1]
    threshold_polish = _run(
        model,
        progress,
        initial_full_design=threshold_start,
        name="threshold_height_reoptimization",
        fixed_topology=True,
        frozen_density=binary,
        nonlinear=True,
        penalty=final_penalty,
    )
    if not threshold_polish.accepted:
        raise RuntimeError(
            "threshold re-optimization was not accepted: "
            f"success={threshold_polish.result.success}, "
            f"max_g={threshold_polish.max_scaled_constraint:.6g}"
        )

    kkt_seed, seed_label = _strictly_feasible_kkt_seed(
        model,
        binary,
        threshold_polish.full_design,
        final_penalty,
    )
    kkt = _run(
        model,
        progress,
        initial_full_design=kkt_seed,
        name="trust_constr_kkt_polish",
        fixed_topology=True,
        frozen_density=binary,
        nonlinear=True,
        penalty=final_penalty,
        method="trust-constr",
        max_iterations=500,
    )
    if not kkt.accepted:
        raise RuntimeError(
            "trust-constr KKT polish was not accepted: "
            f"success={kkt.result.success}, max_g={kkt.max_scaled_constraint:.6g}"
        )

    return CampaignResult(
        linear_fixed=linear,
        fixed_start_runs=tuple(fixed_runs),
        nonlinear_fixed=nonlinear,
        topology_start_runs=tuple(topology_runs),
        continuation=tuple(continuation),
        threshold_polish=threshold_polish,
        kkt_polish=kkt,
        binary_density=binary,
        kkt_seed_label=seed_label,
        elapsed_seconds=perf_counter() - started_at,
    )


def _number(value: object) -> float | int | None:
    if value is None:
        return None
    number = float(value)
    return number if np.isfinite(number) else None


def _run_record(model: HeatSinkModel, run: OptimizationRun, role: str) -> dict:
    heights, raw_density, filtered = model.split_design(run.full_design)
    initial_heights, initial_raw, initial_filtered = model.split_design(
        run.initial_design
    )
    result = run.result
    history = []
    for index, (design, mass, margins, elapsed) in enumerate(
        zip(
            run.history.designs,
            run.history.mass_kg,
            run.history.constraint_margins,
            run.history.elapsed_seconds,
        )
    ):
        history.append(
            {
                "iteration": index,
                "elapsed_seconds": float(elapsed),
                "mass_kg": float(mass),
                "constraint_margins": [float(value) for value in margins],
                "design": [float(value) for value in design],
            }
        )
    record = {
        "name": run.name,
        "role": role,
        "method": run.method,
        "fixed_topology": run.fixed_topology,
        "nonlinear": run.nonlinear,
        "simp_penalty": run.penalty,
        "elapsed_seconds": run.elapsed_seconds,
        "solver_success": bool(result.success),
        "accepted": run.accepted,
        "feasible": run.feasible,
        "status_code": int(result.status),
        "message": str(result.message),
        "iterations": int(getattr(result, "nit", 0)),
        "function_evaluations": int(getattr(result, "nfev", 0)),
        "gradient_evaluations": int(getattr(result, "njev", 0)),
        "mass_kg": run.mass_kg,
        "max_scaled_constraint": run.max_scaled_constraint,
        "feasibility_tolerance": run.feasibility_tolerance,
        "initial_design": {
            "heights_m": initial_heights.tolist(),
            "raw_density": initial_raw.tolist(),
            "filtered_density": initial_filtered.tolist(),
        },
        "final_design": {
            "heights_m": heights.tolist(),
            "raw_density": raw_density.tolist(),
            "filtered_density": filtered.tolist(),
        },
        "density_metrics": {
            "intermediate_count_0p01_0p99": intermediate_density_count(raw_density),
            "grayness": grayness(raw_density),
        },
        "load_cases": [
            {
                "name": case.name,
                "ks_temperature_k": response.ks_temperature_k,
                "limit_k": case.chip_limit_k,
                "scaled_constraint": response.scaled_constraint,
                "constraint_margin": -response.scaled_constraint,
                "feasible": response.scaled_constraint
                <= run.feasibility_tolerance,
                "newton_converged": response.solve.converged,
                "newton_iterations": response.solve.iterations,
                "energy_imbalance_w": response.solve.energy_imbalance_w,
            }
            for case, response in zip(model.config.load_cases, run.responses)
        ],
        "history": history,
    }
    for key in (
        "optimality",
        "constr_violation",
        "physical_stationarity_inf_norm",
        "constraint_complementarity_inf_norm",
        "bound_complementarity_inf_norm",
    ):
        if hasattr(result, key):
            record[key] = _number(getattr(result, key))
    if hasattr(result, "constraint_multipliers"):
        record["constraint_multipliers_normalized_objective"] = np.asarray(
            result.constraint_multipliers
        ).tolist()
        record["constraint_multipliers_mass_kg"] = (
            -np.asarray(result.constraint_multipliers)
            * model.mass_kg(model.initial_design())
        ).tolist()
    if hasattr(result, "physical_bound_multipliers"):
        record["bound_multipliers_physical"] = np.asarray(
            result.physical_bound_multipliers
        ).tolist()
    return record


def _single_fin_removal_screen(model: HeatSinkModel, penalty: float) -> list[dict]:
    """Evaluate every one-fin deletion at the maximum admissible height."""

    count = model.config.geometry.candidate_fins
    height = model.config.geometry.fin_height_bounds_m[1]
    floor = float(model.config.raw["optimization"]["simp_density_floor"])
    records = []
    for index in range(count):
        raw_density = np.ones(count)
        raw_density[index] = floor
        design = np.r_[np.full(count, height), raw_density]
        constraints = []
        for case in model.config.load_cases:
            solved = model.solve(
                design,
                case,
                nonlinear=True,
                penalty=penalty,
            )
            ks_temperature, _ = model.ks_temperature(solved.temperature_k)
            constraints.append(ks_temperature / case.chip_limit_k - 1.0)
        records.append(
            {
                "removed_fin_index": index,
                "scaled_constraints": [float(value) for value in constraints],
                "max_scaled_constraint": float(max(constraints)),
                "filtered_density": model.split_design(design)[2].tolist(),
            }
        )
    return records


def campaign_evidence(model: HeatSinkModel, campaign: CampaignResult) -> dict:
    all_runs: list[tuple[OptimizationRun, str]] = [
        (campaign.linear_fixed, "linear_fixed_reference"),
        *[(run, "nonlinear_fixed_start") for run in campaign.fixed_start_runs],
        *[(run, "topology_start") for run in campaign.topology_start_runs],
        *[(run, "simp_continuation") for run in campaign.continuation[1:]],
        (campaign.threshold_polish, "threshold_height_reoptimization"),
        (campaign.kkt_polish, "kkt_polish"),
    ]
    final_topology = campaign.continuation[-1]
    count = model.config.geometry.candidate_fins
    raw_density = final_topology.full_design[count:]
    threshold_filtered_density = model.split_design(
        campaign.threshold_polish.full_design
    )[2]
    removal_screen = _single_fin_removal_screen(model, final_topology.penalty)
    kkt = campaign.kkt_polish
    active_tolerance = float(
        model.config.raw["optimization"]["scaled_feasibility_tolerance"]
    )
    multipliers = np.asarray(
        getattr(kkt.result, "constraint_multipliers", np.full(len(kkt.responses), np.nan))
    )
    active_constraints = []
    for index, (case, response) in enumerate(
        zip(model.config.load_cases, kkt.responses)
    ):
        if abs(response.scaled_constraint) <= active_tolerance:
            active_constraints.append(
                {
                    "name": case.name,
                    "scaled_constraint": response.scaled_constraint,
                    "normalized_objective_multiplier": (
                        -float(multipliers[index])
                        if np.isfinite(multipliers[index])
                        else None
                    ),
                    "mass_kg_per_unit_scaled_relaxation": (
                        -float(multipliers[index])
                        * model.mass_kg(model.initial_design())
                        if np.isfinite(multipliers[index])
                        else None
                    ),
                }
            )
    core_runs = [
        campaign.nonlinear_fixed,
        *campaign.continuation,
        campaign.threshold_polish,
        campaign.kkt_polish,
    ]
    core_complete = all(run.accepted for run in core_runs)
    near_binary = (
        intermediate_density_count(raw_density) == 0
        and intermediate_density_count(threshold_filtered_density) == 0
    )
    topology_bonus_demonstrated = bool(
        np.count_nonzero(campaign.binary_density > 0.5) < count and near_binary
    )
    blockers = []
    if not campaign.linear_fixed.accepted:
        blockers.append(
            "The linear comparison did not produce an accepted feasible design."
        )
    if not topology_bonus_demonstrated:
        blockers.append(
            "No fin vanishes in the selected topology. The one-fin screen uses "
            "filtered densities and does not establish feasibility of a physically removed fin."
        )
    status = "complete" if core_complete and near_binary else "failed"
    if status == "complete" and blockers:
        status = "complete_with_authoritative_model_blockers"
    return {
        "schema_version": 1,
        "status": status,
        "campaign_elapsed_seconds": campaign.elapsed_seconds,
        "feasibility_tolerance": active_tolerance,
        "blockers": blockers,
        "starting_points": {
            "fixed_topology": [run.name for run in campaign.fixed_start_runs],
            "selected_fixed_topology": campaign.nonlinear_fixed.name,
            "topology": [run.name for run in campaign.topology_start_runs],
            "selected_topology": campaign.continuation[0].name,
            "kkt_seed": campaign.kkt_seed_label,
        },
        "runs": [_run_record(model, run, role) for run, role in all_runs],
        "comparisons": {
            "linear_reference_feasible": campaign.linear_fixed.feasible,
            "linear_reference_max_scaled_constraint": (
                campaign.linear_fixed.max_scaled_constraint
            ),
            "linear_reference_mass_kg": campaign.linear_fixed.mass_kg,
            "nonlinear_fixed_mass_kg": campaign.nonlinear_fixed.mass_kg,
            "topology_continuation_mass_kg": final_topology.mass_kg,
            "threshold_reoptimized_mass_kg": campaign.threshold_polish.mass_kg,
            "kkt_polished_mass_kg": campaign.kkt_polish.mass_kg,
            "topology_vs_nonlinear_fixed_mass_change_kg": (
                final_topology.mass_kg - campaign.nonlinear_fixed.mass_kg
            ),
            "topology_vs_nonlinear_fixed_mass_change_fraction": (
                final_topology.mass_kg / campaign.nonlinear_fixed.mass_kg - 1.0
            ),
        },
        "topology": {
            "candidate_fins": count,
            "raw_density": raw_density.tolist(),
            "filtered_density": model.split_design(final_topology.full_design)[2].tolist(),
            "binary_density": campaign.binary_density.tolist(),
            "threshold_filtered_density": threshold_filtered_density.tolist(),
            "active_fins_after_threshold": int(
                np.count_nonzero(campaign.binary_density > 0.5)
            ),
            "intermediate_count_0p01_0p99": intermediate_density_count(raw_density),
            "threshold_filtered_intermediate_count_0p01_0p99": (
                intermediate_density_count(threshold_filtered_density)
            ),
            "grayness": grayness(raw_density),
            "threshold_filtered_grayness": grayness(threshold_filtered_density),
            "topology_bonus_demonstrated": topology_bonus_demonstrated,
            "any_single_fin_removal_feasible": any(
                record["max_scaled_constraint"] <= active_tolerance
                for record in removal_screen
            ),
            "single_fin_removal_screen": removal_screen,
        },
        "kkt": {
            "active_constraint_tolerance": active_tolerance,
            "active_constraints": active_constraints,
            "stationarity_inf_norm_physical": _number(
                getattr(kkt.result, "physical_stationarity_inf_norm", None)
            ),
            "constraint_complementarity_inf_norm": _number(
                getattr(kkt.result, "constraint_complementarity_inf_norm", None)
            ),
            "bound_complementarity_inf_norm": _number(
                getattr(kkt.result, "bound_complementarity_inf_norm", None)
            ),
            "constraint_violation": _number(
                getattr(kkt.result, "constr_violation", None)
            ),
        },
    }


def write_campaign_evidence(evidence: dict, directory: str | Path) -> None:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "campaign.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Optimization and topology campaign",
        "",
        f"Status: **{evidence['status']}**",
        "",
        f"Campaign runtime: {evidence['campaign_elapsed_seconds']:.3f} s.",
        "",
        "## Runs",
        "",
        "| Run | Role | Method | Success | Accepted | Mass (kg) | Max scaled constraint | Iterations | Time (s) |",
        "|---|---|---|:---:|:---:|---:|---:|---:|---:|",
    ]
    for run in evidence["runs"]:
        lines.append(
            f"| {run['name']} | {run['role']} | {run['method']} | "
            f"{'PASS' if run['solver_success'] else 'FAIL'} | "
            f"{'PASS' if run['accepted'] else 'FAIL'} | {run['mass_kg']:.10g} | "
            f"{run['max_scaled_constraint']:.6g} | {run['iterations']} | "
            f"{run['elapsed_seconds']:.3f} |"
        )
    comparison = evidence["comparisons"]
    topology = evidence["topology"]
    lines.extend(
        [
            "",
            "## Comparisons",
            "",
            f"- Linear fixed-topology feasibility: **{comparison['linear_reference_feasible']}** "
            f"(maximum scaled constraint {comparison['linear_reference_max_scaled_constraint']:.6g}).",
            f"- Nonlinear fixed-topology mass: {comparison['nonlinear_fixed_mass_kg']:.10g} kg.",
            f"- Final topology-continuation mass: {comparison['topology_continuation_mass_kg']:.10g} kg.",
            f"- Thresholded/re-optimized mass: {comparison['threshold_reoptimized_mass_kg']:.10g} kg.",
            f"- KKT-polished mass: {comparison['kkt_polished_mass_kg']:.10g} kg.",
            f"- Topology mass change relative to nonlinear fixed topology: "
            f"{comparison['topology_vs_nonlinear_fixed_mass_change_kg']:.6g} kg "
            f"({comparison['topology_vs_nonlinear_fixed_mass_change_fraction']:.6%}).",
            "",
            "## Topology",
            "",
            f"- Active fins after threshold: {topology['active_fins_after_threshold']} / "
            f"{topology['candidate_fins']}.",
            f"- Intermediate raw densities in (0.01, 0.99): "
            f"{topology['intermediate_count_0p01_0p99']}.",
            f"- Intermediate filtered densities after thresholding: "
            f"{topology['threshold_filtered_intermediate_count_0p01_0p99']}.",
            f"- Grayness metric: {topology['grayness']:.6g}.",
            f"- Topology bonus demonstrated by a vanished fin: "
            f"**{topology['topology_bonus_demonstrated']}**.",
            f"- Any single-fin deletion feasible at maximum height: "
            f"**{topology['any_single_fin_removal_feasible']}**.",
            "",
            "## KKT evidence",
            "",
            f"- Physical stationarity infinity norm: "
            f"{evidence['kkt']['stationarity_inf_norm_physical']}.",
            f"- Constraint complementarity infinity norm: "
            f"{evidence['kkt']['constraint_complementarity_inf_norm']}.",
            f"- Bound complementarity infinity norm: "
            f"{evidence['kkt']['bound_complementarity_inf_norm']}.",
            f"- Constraint violation: {evidence['kkt']['constraint_violation']}.",
            "",
            "| Active constraint | Scaled value | Normalized multiplier | kg per unit scaled relaxation |",
            "|---|---:|---:|---:|",
        ]
    )
    for active in evidence["kkt"]["active_constraints"]:
        lines.append(
            f"| {active['name']} | {active['scaled_constraint']:.6g} | "
            f"{active['normalized_objective_multiplier']:.6g} | "
            f"{active['mass_kg_per_unit_scaled_relaxation']:.6g} |"
        )
    lines.extend(
        [
            "",
            "The single-fin screen lowers one raw density and retains the density "
            "filter; it is not a reanalysis of a physically removed fin. Interpret "
            "the results accordingly and do not claim a vanished-fin bonus without "
            "a feasible discrete reanalysis.",
            "",
            "All values in this report are generated from `campaign.json` by the campaign command.",
        ]
    )
    (destination / "campaign.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _progress(run: OptimizationRun) -> None:
    print(
        f"{run.name}: success={bool(run.result.success)}, "
        f"accepted={run.accepted}, mass={run.mass_kg:.10g} kg, "
        f"max_g={run.max_scaled_constraint:.6g}, "
        f"time={run.elapsed_seconds:.3f} s",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="Project4/config.yaml")
    parser.add_argument("--output", default="Project4/results/optimization")
    arguments = parser.parse_args()
    config_path = Path(arguments.config).resolve()
    try:
        require_human_approvals(config_path.parent)
    except HumanGateError as error:
        print(f"HUMAN GATE: {error}")
        return 2
    model = HeatSinkModel(load_config(config_path))
    campaign = run_campaign(model, progress=_progress)
    evidence = campaign_evidence(model, campaign)
    write_campaign_evidence(evidence, arguments.output)
    print(
        f"Campaign evidence written to {Path(arguments.output).resolve()} "
        f"with status {evidence['status']}."
    )
    return 0 if evidence["status"].startswith("complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())

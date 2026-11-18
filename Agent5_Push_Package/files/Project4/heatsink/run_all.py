"""Single entry point for verification, optimization, and report data."""

from __future__ import annotations

import argparse
from math import isfinite
from pathlib import Path

from .config import load_config
from .gates import HumanGateError, require_human_approvals
from .model import HeatSinkModel
from .campaign import CampaignResult, run_campaign
from .serialize import final_payload, write_json
from .verification import (
    sensitivity_cost_comparison,
    objective_gradient_checks,
    student_truth_summary,
    taylor_checks,
    write_sensitivity_evidence,
)
from .benchmark_verification import benchmark_verification, write_evidence
from .site import build_site


class CampaignAcceptanceError(RuntimeError):
    """A completed optimization stage does not satisfy fixed acceptance rules."""


def _require_accepted_campaign(
    model: HeatSinkModel, campaign: CampaignResult
) -> None:
    tolerance = float(
        model.config.raw["optimization"]["scaled_feasibility_tolerance"]
    )
    runs = (
        campaign.linear_fixed,
        campaign.nonlinear_fixed,
        *campaign.continuation,
        campaign.threshold_polish,
        campaign.kkt_polish,
    )
    for run in runs:
        constraints = [float(response.scaled_constraint) for response in run.responses]
        if not constraints or not all(isfinite(value) for value in constraints):
            raise CampaignAcceptanceError(
                f"{run.name} produced missing or non-finite constraints"
            )
        maximum_violation = max(constraints)
        if not bool(run.result.success) or maximum_violation > tolerance:
            raise CampaignAcceptanceError(
                f"{run.name}: success={bool(run.result.success)}, "
                f"maximum scaled constraint={maximum_violation:.6g}, "
                f"fixed tolerance={tolerance:.6g}, message={run.result.message}"
            )

    density_floor = float(model.config.raw["optimization"]["simp_density_floor"])
    binary_density = campaign.binary_density.tolist()
    allowed = {density_floor, 1.0}
    if not set(binary_density).issubset(allowed):
        raise CampaignAcceptanceError(
            "thresholded raw densities are not exactly the configured density floor or one"
        )
    if density_floor not in binary_density or 1.0 not in binary_density:
        raise CampaignAcceptanceError(
            "the topology stage did not demonstrate both removed and retained fins"
        )
    _, _, physical_density = model.split_design(campaign.kkt_polish.full_design)
    if not set(physical_density.tolist()).issubset(allowed):
        raise CampaignAcceptanceError(
            "the final physical densities are not binary after density filtering; "
            "a discrete retained-fin reanalysis is required"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="Project4/config.yaml")
    parser.add_argument(
        "--check-gates", action="store_true", help="validate human inputs and exit"
    )
    arguments = parser.parse_args()
    config_path = Path(arguments.config).resolve()
    project_directory = config_path.parent
    config = load_config(config_path)
    model = HeatSinkModel(config)
    print(
        f"Configured {model.ndof} thermal DOFs and "
        f"{2 * config.geometry.candidate_fins} design variables."
    )
    try:
        _, truth = require_human_approvals(project_directory)
    except HumanGateError as error:
        print(f"HUMAN GATE: {error}")
        print(f"Complete {project_directory / 'HUMAN_BENCHMARK_WORKSHEET.md'}")
        print(f"Approve {project_directory / 'SPECIFICATION.md'}")
        return 2
    if arguments.check_gates:
        print("Human gates passed.")
        return 0
    print("Human gates passed. Running adjoint verification and optimization campaign.")
    verification = benchmark_verification(model, truth)
    verification_directory = project_directory / "results" / "verification"
    write_evidence(verification, verification_directory)
    if verification["status"] != "passed":
        print(f"VERIFICATION FAILED: see {verification_directory / 'verification.md'}")
        return 3
    start = model.initial_design(0.030)
    start[config.geometry.candidate_fins:] = 0.60
    gradients = taylor_checks(model, start)
    cost = sensitivity_cost_comparison(model, start)
    objective_gradients = objective_gradient_checks(model, start)
    sensitivity = write_sensitivity_evidence(
        gradients, objective_gradients, cost, project_directory / "results" / "sensitivity"
    )
    if sensitivity["status"] != "passed":
        print("V7 SENSITIVITY VERIFICATION FAILED")
        return 4
    try:
        campaign = run_campaign(model)
        _require_accepted_campaign(model, campaign)
    except (CampaignAcceptanceError, RuntimeError, ValueError) as error:
        print(f"OPTIMIZATION CAMPAIGN FAILED: {error}")
        print("No final results.json was written. See GitHub issue #10 (P4-A3).")
        return 5
    payload = final_payload(
        model,
        campaign,
        {**student_truth_summary(truth), **verification},
        gradients,
        cost,
    )
    destination = Path(config.raw["outputs"]["results_json"])
    if not destination.is_absolute():
        destination = project_directory.parent / destination
    write_json(payload, destination)
    build_site(project_directory / "site")
    print(f"Final results written to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

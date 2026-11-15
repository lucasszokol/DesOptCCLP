"""Single entry point for verification, optimization, and report data."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .gates import HumanGateError, require_human_approvals
from .model import HeatSinkModel
from .campaign import run_campaign
from .serialize import final_payload, write_json, validate_final_payload
from .verification import (
    sensitivity_cost_comparison,
    objective_gradient_checks,
    student_truth_summary,
    taylor_checks,
    write_sensitivity_evidence,
)
from .benchmark_verification import benchmark_verification, write_evidence
from .site import build_site
from .uncertainty import run_uncertainty
from .serialize import _design_view


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
    campaign = run_campaign(model)
    tolerance = float(config.raw["optimization"]["scaled_feasibility_tolerance"])
    required_runs = (campaign.linear_fixed, campaign.nonlinear_fixed, campaign.threshold_polish, campaign.kkt_polish)
    for run in required_runs:
        violation = max(response.scaled_constraint for response in run.responses)
        if not run.result.success or violation > tolerance:
            print(f"OPTIMIZATION FAILED: {run.name}: {run.result.message}; "
                  f"maximum scaled constraint = {violation:.6g} (tolerance {tolerance:.6g})")
            return 5
    robust_model, robust_run, robust_checks = run_uncertainty(model, campaign.kkt_polish.full_design)
    robust_violation = max(r.scaled_constraint for r in robust_run.responses)
    if (not robust_run.result.success or robust_violation > tolerance or
            any(check["relative_error"] > config.raw["verification"]["gradient_relative_tolerance"] for check in robust_checks)):
        print(f"UNCERTAINTY STUDY FAILED: {robust_run.result.message}; maximum constraint {robust_violation:.6g}")
        return 6
    payload = final_payload(
        model,
        campaign,
        {**student_truth_summary(truth), **verification},
        gradients,
        cost,
    )
    payload["uncertainty"] = {
        "assumptions": config.raw["uncertainty"],
        "description": "Paired low and high power and ambient scenarios for each load case; illustrative bounded scenarios, not a probability model.",
        "design": _design_view(robust_model, "Uncertainty scenario optimum", robust_run.full_design, True),
        "baseline_design": _design_view(robust_model, "Nominal optimum under uncertainty", campaign.kkt_polish.full_design, True),
        "optimizer_success": bool(robust_run.result.success),
        "optimizer_message": str(robust_run.result.message),
        "gradient_checks": robust_checks,
    }
    validate_final_payload(payload, project_directory / "site" / "assets" / "results.schema.json",
                           tolerance, float(config.raw["verification"]["gradient_relative_tolerance"]))
    destination = Path(config.raw["outputs"]["results_json"])
    write_json(payload, destination)
    build_site(project_directory / "site")
    print(f"Final results written to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

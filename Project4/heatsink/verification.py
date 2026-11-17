"""Student-truth ingestion plus discrete-adjoint verification."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .model import HeatSinkModel


def _constraint_value(model, design, case, nonlinear, penalty):
    """Independent state-only evaluation: never compute an adjoint for FD."""
    solved = model.solve(design, case, nonlinear=nonlinear, penalty=penalty)
    if not solved.converged:
        raise RuntimeError(f"finite-difference state failed: {case.name}")
    return model.ks_temperature(solved.temperature_k)[0] / case.chip_limit_k - 1.0


def taylor_checks(
    model: HeatSinkModel, design: np.ndarray, *, nonlinear: bool = True,
    penalty: float = 3.0, random_directions: int = 2, seed: int = 20261112,
) -> list[dict]:
    """Central differences and second-order Taylor remainders for every case."""

    count = model.config.geometry.candidate_fins
    base_design = np.asarray(design, dtype=float).copy()
    if np.any(base_design[count:] <= 0.2) or np.any(base_design[count:] >= 0.8):
        raise ValueError("Taylor checks require interior density values in (0.2, 0.8)")
    rng = np.random.default_rng(seed)
    index = np.arange(count, dtype=float)
    directions = [
        ("height", "structured", np.r_[np.linspace(0.001, 0.004, count) * (1.0 + 0.12 * np.sin(index)), np.zeros(count)]),
        ("density", "structured", np.r_[np.zeros(count), -np.linspace(0.05, 0.20, count) * (1.0 + 0.10 * np.cos(index))]),
    ]
    for number in range(random_directions):
        for family, scale in (("height", 0.004), ("density", 0.20)):
            values = rng.normal(size=count)
            values *= scale / np.max(np.abs(values))
            direction = np.r_[values, np.zeros(count)] if family == "height" else np.r_[np.zeros(count), values]
            directions.append((family, f"random_{number}", direction))
    g = model.config.geometry
    lower = np.r_[np.full(count, g.fin_height_bounds_m[0]), np.full(count, g.density_bounds[0])]
    upper = np.r_[np.full(count, g.fin_height_bounds_m[1]), np.full(count, g.density_bounds[1])]
    for _, _, direction in directions:
        if np.any(base_design - np.abs(direction) < lower) or np.any(base_design + np.abs(direction) > upper):
            raise ValueError("Taylor sweep would leave the design bounds")
    checks: list[dict] = []
    for case in model.config.load_cases:
        response = model.response_with_adjoint(base_design, case, nonlinear=nonlinear, penalty=penalty)
        for family, direction_name, direction in directions:
            derivative = float(response.gradient @ direction)
            rows = []
            for step in np.logspace(0, -5, 11):
                plus = _constraint_value(model, base_design + step * direction, case, nonlinear, penalty)
                minus = _constraint_value(model, base_design - step * direction, case, nonlinear, penalty)
                central = (plus - minus) / (2.0 * step)
                derivative_error = abs(float(central) - derivative)
                relative_derivative_error = derivative_error / max(abs(derivative), 1.0e-15)
                remainder = abs(plus - response.scaled_constraint - step * derivative)
                rows.append(
                    {
                        "step": float(step),
                        "central_derivative": float(central),
                        "adjoint_derivative": derivative,
                        "derivative_absolute_error": derivative_error,
                        "derivative_relative_error": relative_derivative_error,
                        "absolute_error": float(remainder),
                        "zeroth_order_remainder": abs(plus - response.scaled_constraint),
                    }
                )
            # The largest four steps expose the asymptotic O(h^2) remainder;
            # smaller steps are retained to show the eventual roundoff floor.
            slope = float(
                np.polyfit(
                    np.log([row["step"] for row in rows[:4]]),
                    np.log([row["absolute_error"] for row in rows[:4]]),
                    1,
                )[0]
            )
            checks.append(
                {
                    "load_case": case.name,
                    "variable_family": family,
                    "physics": "nonlinear" if nonlinear else "linear",
                    "penalty": penalty,
                    "direction_name": direction_name,
                    "direction": direction.tolist(),
                    "seed": seed,
                    "design": base_design.tolist(),
                    "slope_fit_steps": [row["step"] for row in rows[:4]],
                    "taylor_slope": slope,
                    "minimum_relative_directional_error": min(
                        row["derivative_relative_error"] for row in rows
                    ),
                    "rows": rows,
                }
            )
            checks[-1]["pass"] = bool(
                model.config.raw["verification"]["taylor_slope_bounds"][0]
                <= slope
                <= model.config.raw["verification"]["taylor_slope_bounds"][1]
                and checks[-1]["minimum_relative_directional_error"]
                <= float(model.config.raw["verification"]["gradient_relative_tolerance"])
            )
    return checks


def objective_gradient_checks(model: HeatSinkModel, design: np.ndarray) -> list[dict]:
    """Check both mass-objective variable families independently."""

    count = model.config.geometry.candidate_fins
    gradient = model.mass_gradient(design)
    rows = []
    rng = np.random.default_rng(20261112)
    directions = [
        ("height", "structured", np.r_[np.linspace(0.001, 0.004, count), np.zeros(count)]),
        ("density", "structured", np.r_[np.zeros(count), np.linspace(-0.05, -0.20, count)]),
    ]
    for number in range(2):
        directions.extend([
            ("height", f"random_{number}", np.r_[rng.uniform(-0.004, 0.004, count), np.zeros(count)]),
            ("density", f"random_{number}", np.r_[np.zeros(count), rng.uniform(-0.2, 0.2, count)]),
        ])
    for family, name, direction in directions:
        step = 1.0e-5
        central = (
            model.mass_kg(design + step * direction)
            - model.mass_kg(design - step * direction)
        ) / (2.0 * step)
        analytic = float(gradient @ direction)
        relative = abs(central - analytic) / max(abs(analytic), 1.0e-15)
        rows.append(
            {
                "objective": "mass_kg",
                "direction_name": name,
                "direction": direction.tolist(),
                "variable_family": family,
                "central_derivative": float(central),
                "analytic_derivative": analytic,
                "relative_error": float(relative),
                "pass": bool(
                    relative
                    <= float(model.config.raw["verification"]["gradient_relative_tolerance"])
                ),
            }
        )
    return rows


def sensitivity_cost_comparison(
    model: HeatSinkModel, design: np.ndarray, *, case_index: int = 0,
    nonlinear: bool = True, penalty: float = 3.0,
) -> dict:
    """Measure one all-variable adjoint against a central-difference estimate."""

    case = model.config.load_cases[case_index]
    # Warm both paths before timing; FD below performs state solves only.
    model.response_with_adjoint(design, case, nonlinear=nonlinear, penalty=penalty)
    start = perf_counter()
    response = model.response_with_adjoint(design, case, nonlinear=nonlinear, penalty=penalty)
    adjoint_seconds = perf_counter() - start
    start = perf_counter()
    steps = np.r_[np.full(model.config.geometry.candidate_fins, 1.0e-6), np.full(model.config.geometry.candidate_fins, 1.0e-5)]
    finite = np.zeros(design.size)
    for index in range(design.size):
        perturbation = np.zeros(design.size)
        perturbation[index] = steps[index]
        plus = _constraint_value(model, design + perturbation, case, nonlinear, penalty)
        minus = _constraint_value(model, design - perturbation, case, nonlinear, penalty)
        finite[index] = (plus - minus) / (2.0 * steps[index])
    finite_seconds = perf_counter() - start
    relative_error = np.linalg.norm(finite - response.gradient) / max(np.linalg.norm(finite), 1.0e-15)
    count = model.config.geometry.candidate_fins
    family_errors = {
        family: float(np.linalg.norm(finite[part] - response.gradient[part]) / max(np.linalg.norm(finite[part]), 1.0e-15))
        for family, part in (("height", slice(0, count)), ("density", slice(count, None)))
    }
    return {
        "load_case": case.name,
        "physics": "nonlinear" if nonlinear else "linear",
        "penalty": penalty,
        "finite_difference_steps": steps.tolist(),
        "adjoint_gradient": response.gradient.tolist(),
        "finite_difference_gradient": finite.tolist(),
        "design_variables": int(design.size),
        "adjoint_seconds": adjoint_seconds,
        "finite_difference_seconds": finite_seconds,
        "speedup": finite_seconds / adjoint_seconds,
        "relative_gradient_error": float(relative_error),
        "family_relative_errors": family_errors,
        "adjoint_linear_solves_per_response": 1,
        "finite_difference_adjoint_solves": 0,
        "timing_note": "One warmed measurement of state+adjoint versus state-only central FD; wall times are machine dependent.",
        "central_difference_state_solves": int(2 * design.size),
    }


def student_truth_summary(truth: dict) -> dict:
    """Preserve the submitted truth and attestation without recomputing it."""

    return {
        "status": truth["status"],
        "student_attestation": truth["student_attestation"],
        "benchmarks": {key: truth[key] for key in ("v1", "v2", "v3", "v6")},
    }


def ks_state_checks(model: HeatSinkModel) -> list[dict]:
    """Check all state components, ties, support, and translation invariance."""
    rng = np.random.default_rng(20261112)
    chip = model.chip_dofs()
    states = {
        "uniform_tie": np.full(model.ndof, 340.0),
        "nonuniform": rng.uniform(320.0, 370.0, model.ndof),
        "large_offset": rng.uniform(320.0, 370.0, model.ndof) + 1.0e4,
    }
    records = []
    for name, state in states.items():
        value, gradient = model.ks_temperature(state)
        finite = np.zeros(model.ndof)
        step = 1.0e-3
        for index in range(model.ndof):
            perturbation = np.zeros(model.ndof)
            perturbation[index] = step
            finite[index] = (model.ks_temperature(state + perturbation)[0] - model.ks_temperature(state - perturbation)[0]) / (2.0 * step)
        error = float(np.linalg.norm(gradient - finite) / np.linalg.norm(gradient))
        outside = np.ones(model.ndof, dtype=bool)
        outside[chip] = False
        support_error = float(np.max(np.abs(gradient[outside])))
        sum_error = abs(float(gradient.sum()) - 1.0)
        shift_error = abs(model.ks_temperature(state + 7.0)[0] - value - 7.0)
        tie_error = float(np.max(np.abs(gradient[chip] - 1.0 / len(chip)))) if name == "uniform_tie" else 0.0
        passed = error <= 1.0e-5 and support_error == 0.0 and sum_error <= 1.0e-12 and shift_error <= 1.0e-10 and tie_error <= 1.0e-12
        records.append({"state": name, "relative_error": error, "off_chip_error": support_error,
                        "gradient_sum_error": sum_error, "translation_error_k": shift_error,
                        "tie_weight_error": tie_error, "step_k": step, "pass": bool(passed)})
    return records


def _write_taylor_plot(checks: list[dict], directory: Path) -> None:
    """Plot the recorded sweeps; no reruns or hand-entered numerical values."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    for row, physics in enumerate(("linear", "nonlinear")):
        for column, family in enumerate(("height", "density")):
            axis = axes[row, column]
            subset = [check for check in checks if check["physics"] == physics and check["variable_family"] == family]
            for check in subset:
                steps = np.array([item["step"] for item in check["rows"]])
                errors = np.array([item["absolute_error"] for item in check["rows"]])
                axis.loglog(steps, np.maximum(errors, np.finfo(float).tiny), alpha=0.65, linewidth=1)
            if subset:
                reference = subset[0]["rows"][0]["absolute_error"]
                axis.loglog(steps, reference * steps**2, "k--", label="slope 2 reference")
                axis.legend(fontsize=8)
            axis.set(title=f"{physics.capitalize()}: {family}", xlabel="Dimensionless step", ylabel="First-order Taylor remainder")
            axis.grid(True, which="both", alpha=0.2)
    fig.suptitle("Both load cases, SIMP p = 1, 2, 3; structured and seeded random directions")
    fig.savefig(directory / "taylor_checks.png", dpi=160)
    plt.close(fig)


def write_sensitivity_evidence(
    checks: list[dict], objective_checks: list[dict], cost: dict, directory: Path,
    *, ks_checks: list[dict] | None = None, cost_checks: list[dict] | None = None,
    metadata: dict | None = None,
) -> dict:
    """Write the reproducible V7 payload without manual result transcription."""

    directory.mkdir(parents=True, exist_ok=True)
    passed = (
        bool(checks) and all(check["pass"] for check in checks)
        and bool(objective_checks) and all(check["pass"] for check in objective_checks)
        and cost["relative_gradient_error"] <= 1.0e-5
        and all(check["pass"] for check in (ks_checks or []))
        and all(check["relative_gradient_error"] <= 1.0e-5 and all(error <= 1.0e-5 for error in check["family_relative_errors"].values()) for check in (cost_checks or [cost]))
    )
    payload = {
        "id": "V7", "status": "passed" if passed else "failed",
        "constraint_checks": checks, "objective_checks": objective_checks,
        "cost_comparison": cost,
        "ks_state_checks": ks_checks or [],
        "all_variable_checks": cost_checks or [cost],
        "metadata": metadata or {},
    }
    (directory / "sensitivity.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# V7 adjoint and sensitivity evidence", "",
        f"Status: **{payload['status'].upper()}**", "",
        "The fixed slope window uses the largest four steps, selected before observing errors. All smaller steps are retained in JSON to expose cancellation/roundoff. No tolerance is fitted to results.", "",
        "| Physics / p | Response | Direction | Variable family | Taylor slope | Best relative directional error | Pass |",
        "|---|---|---|---|---:|---:|:---:|",
    ]
    lines.extend(
        f"| {check.get('physics', 'nonlinear')} / {check.get('penalty', 3)} | {check['load_case']} constraint | {check.get('direction_name', 'structured')} | {check['variable_family']} | "
        f"{check['taylor_slope']:.6g} | {check['minimum_relative_directional_error']:.3g} | "
        f"{'PASS' if check['pass'] else 'FAIL'} |"
        for check in checks
    )
    lines.extend(["", "| Objective | Direction | Variable family | Relative error | Pass |", "|---|---|---|---:|:---:|"])
    lines.extend(
        f"| mass | {check['direction_name']} | {check['variable_family']} | {check['relative_error']:.3g} | "
        f"{'PASS' if check['pass'] else 'FAIL'} |"
        for check in objective_checks
    )
    if ks_checks:
        lines.extend(["", "| KS state | Relative derivative error | Pass |", "|---|---:|:---:|"])
        lines.extend(f"| {row['state']} | {row['relative_error']:.6g} | {'PASS' if row['pass'] else 'FAIL'} |" for row in ks_checks)
    if cost_checks:
        lines.extend(["", "| Physics | Load | Full-gradient relative error | State + adjoint (s) | State-only FD (s) | Speedup |", "|---|---|---:|---:|---:|---:|"])
        lines.extend(f"| {row['physics']} | {row['load_case']} | {row['relative_gradient_error']:.6g} | {row['adjoint_seconds']:.4g} | {row['finite_difference_seconds']:.4g} | {row['speedup']:.3g} |" for row in cost_checks)
    lines.extend(["", "Finite differences compute no adjoints. Timings are single warmed measurements, not a portable performance guarantee. Mass is state independent, so its exact direct gradient needs no adjoint solve."])
    lines.extend(
        [
            "", f"Adjoint/finite-difference relative gradient error: `{cost['relative_gradient_error']:.6g}`.",
            f"Measured speedup: `{cost['speedup']:.3g}x` ({cost['central_difference_state_solves']} central-difference state solves).",
        ]
    )
    (directory / "sensitivity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    """Regenerate Agent 2 evidence without executing the optimization campaign."""
    import argparse
    import hashlib
    import platform
    import subprocess
    import scipy
    from .config import load_config
    from .gates import require_human_approvals

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="Project4/config.yaml")
    arguments = parser.parse_args()
    path = Path(arguments.config).resolve()
    require_human_approvals(path.parent)
    model = HeatSinkModel(load_config(path))
    count = model.config.geometry.candidate_fins
    # Break reflection symmetry and exercise the nonuniform density filter.
    design = np.r_[np.linspace(0.025, 0.040, count), np.linspace(0.45, 0.65, count)]
    checks = []
    for nonlinear in (False, True):
        for penalty in model.config.raw["optimization"]["simp_penalties"]:
            print(f"Taylor checks: nonlinear={nonlinear}, p={penalty}", flush=True)
            checks.extend(taylor_checks(model, design, nonlinear=nonlinear, penalty=float(penalty)))
    costs = [sensitivity_cost_comparison(model, design, nonlinear=mode, case_index=i)
             for mode in (False, True) for i in range(len(model.config.load_cases))]
    sources = [Path(__file__).resolve(), Path(__file__).resolve().with_name("model.py"), Path(__file__).resolve().with_name("topology.py"), path]
    metadata = {
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "platform": platform.platform(), "dtype": "float64", "seed": 20261112,
        "design": design.tolist(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path.parent, text=True).strip(),
        "source_sha256": {str(p.relative_to(path.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "command": "python -m Project4.heatsink.verification --config Project4/config.yaml",
    }
    payload = write_sensitivity_evidence(checks, objective_gradient_checks(model, design), costs[2],
        path.parent / "results" / "sensitivity", ks_checks=ks_state_checks(model), cost_checks=costs, metadata=metadata)
    _write_taylor_plot(checks, path.parent / "results" / "sensitivity")
    print(f"Sensitivity evidence: {payload['status']}", flush=True)
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Independent V1--V7 verification calculations and evidence generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from .elements import line_conduction_matrix, quad4_conduction_matrix
from .config import load_config
from .model import HeatSinkModel


def _comparison(name: str, computed: float, exact: float, tolerance: float) -> dict:
    absolute = abs(computed - exact)
    relative = absolute / max(abs(exact), 1.0e-15)
    return {
        "quantity": name,
        "computed": float(computed),
        "exact": float(exact),
        "absolute_error": float(absolute),
        "relative_error": float(relative),
        "tolerance": float(tolerance),
        "pass": bool(absolute <= tolerance),
    }


def verify_v1(truth: dict) -> dict:
    """Solve a four-element bar and compare quarter-point values and reaction."""

    length, area, conductivity = 0.040, 5.0e-5, 167.0
    nodes = np.linspace(0.0, length, 5)
    matrix = np.zeros((5, 5))
    for i in range(4):
        element = np.array([i, i + 1])
        matrix[np.ix_(element, element)] += line_conduction_matrix(
            conductivity, area, nodes[i + 1] - nodes[i]
        )
    temperature = np.zeros(5)
    temperature[[0, -1]] = [373.15, 293.15]
    free = np.arange(1, 4)
    fixed = np.array([0, 4])
    temperature[free] = np.linalg.solve(
        matrix[np.ix_(free, free)],
        -matrix[np.ix_(free, fixed)] @ temperature[fixed],
    )
    submitted = truth["temperatures_k"]
    checks = [
        _comparison(f"T({fraction}L)", temperature[i], submitted[i - 1], 5.0e-9)
        for i, fraction in enumerate(("1/4", "1/2", "3/4"), start=1)
    ]
    outward = float(-(matrix @ temperature)[-1])
    checks.append(
        _comparison("outward heat rate", outward, truth["outward_heat_rate_w"], 5.0e-9)
    )
    return {"id": "V1", "name": "1D conduction bar", "checks": checks}


def verify_v2(truth: dict, elements: int = 200) -> dict:
    """Solve the adiabatic-tip fin with independent 1D FE assembly."""

    length, k, width, thickness, h = 0.050, 167.0, 0.050, 0.001, 10.0
    area, perimeter = width * thickness, 2.0 * (width + thickness)
    element_length = length / elements
    matrix = np.zeros((elements + 1, elements + 1))
    for i in range(elements):
        dofs = np.array([i, i + 1])
        local = line_conduction_matrix(k, area, element_length)
        local += h * perimeter * element_length / 6.0 * np.array([[2.0, 1.0], [1.0, 2.0]])
        matrix[np.ix_(dofs, dofs)] += local
    excess = np.zeros(elements + 1)
    excess[0] = 353.15 - 298.15
    excess[1:] = np.linalg.solve(matrix[1:, 1:], -matrix[1:, :1].ravel() * excess[0])
    reaction = float((matrix @ excess)[0])
    m_value = float(np.sqrt(h * perimeter / (k * area)))
    checks = [
        _comparison("m", m_value, truth["m_per_m"], 5.0e-4),
        _comparison("tip temperature", 298.15 + excess[-1], truth["tip_temperature_k"], 5.0e-4),
        _comparison("base heat rate", reaction, truth["base_heat_rate_w"], 5.0e-4),
    ]
    return {"id": "V2", "name": "straight fin", "checks": checks}


def _manufactured_error(elements: int) -> tuple[float, float]:
    """Return Q1 FE L2 and energy-seminorm errors on a uniform square mesh."""

    count = (elements + 1) ** 2
    coordinates = np.array(
        [(x / elements, z / elements) for z in range(elements + 1) for x in range(elements + 1)]
    )
    matrix = np.zeros((count, count))
    load = np.zeros(count)
    gauss = (-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))
    quads: list[np.ndarray] = []
    for iz in range(elements):
        for ix in range(elements):
            dofs = np.array([
                iz * (elements + 1) + ix,
                iz * (elements + 1) + ix + 1,
                (iz + 1) * (elements + 1) + ix + 1,
                (iz + 1) * (elements + 1) + ix,
            ])
            quads.append(dofs)
            xy = coordinates[dofs]
            matrix[np.ix_(dofs, dofs)] += quad4_conduction_matrix(xy, 1.0, 1.0)
            local_load = np.zeros(4)
            for xi in gauss:
                for eta in gauss:
                    shape = 0.25 * np.array([
                        (1 - xi) * (1 - eta), (1 + xi) * (1 - eta),
                        (1 + xi) * (1 + eta), (1 - xi) * (1 + eta),
                    ])
                    dnatural = 0.25 * np.array([
                        [-(1-eta), +(1-eta), +(1+eta), -(1+eta)],
                        [-(1-xi), -(1+xi), +(1+xi), +(1-xi)],
                    ])
                    jacobian = dnatural @ xy
                    point = shape @ xy
                    source = 2.0 * np.pi**2 * np.sin(np.pi * point[0]) * np.sin(np.pi * point[1])
                    local_load += np.linalg.det(jacobian) * shape * source
            load[dofs] += local_load
    boundary = np.flatnonzero(
        np.isclose(coordinates[:, 0], 0.0) | np.isclose(coordinates[:, 0], 1.0)
        | np.isclose(coordinates[:, 1], 0.0) | np.isclose(coordinates[:, 1], 1.0)
    )
    free = np.setdiff1d(np.arange(count), boundary)
    temperature = np.full(count, 300.0)
    temperature[free] = np.linalg.solve(
        matrix[np.ix_(free, free)], load[free] - matrix[np.ix_(free, boundary)] @ temperature[boundary]
    )
    l2_squared = 0.0
    energy_squared = 0.0
    for dofs in quads:
        xy = coordinates[dofs]
        for xi in gauss:
            for eta in gauss:
                shape = 0.25 * np.array([
                    (1-xi)*(1-eta), (1+xi)*(1-eta),
                    (1+xi)*(1+eta), (1-xi)*(1+eta),
                ])
                dnatural = 0.25 * np.array([
                    [-(1-eta), +(1-eta), +(1+eta), -(1+eta)],
                    [-(1-xi), -(1+xi), +(1+xi), +(1-xi)],
                ])
                jacobian = dnatural @ xy
                gradient = np.linalg.solve(jacobian, dnatural)
                point = shape @ xy
                exact = 300.0 + np.sin(np.pi * point[0]) * np.sin(np.pi * point[1])
                exact_gradient = np.array([
                    np.pi * np.cos(np.pi * point[0]) * np.sin(np.pi * point[1]),
                    np.pi * np.sin(np.pi * point[0]) * np.cos(np.pi * point[1]),
                ])
                determinant = np.linalg.det(jacobian)
                l2_squared += determinant * (shape @ temperature[dofs] - exact) ** 2
                energy_squared += determinant * np.sum((gradient @ temperature[dofs] - exact_gradient) ** 2)
    return float(np.sqrt(l2_squared)), float(np.sqrt(energy_squared))


def verify_v3(truth: dict) -> dict:
    meshes = np.array([4, 8, 16])
    errors = np.array([_manufactured_error(int(n)) for n in meshes])
    h = 1.0 / meshes
    l2_slope = float(np.polyfit(np.log(h), np.log(errors[:, 0]), 1)[0])
    energy_slope = float(np.polyfit(np.log(h), np.log(errors[:, 1]), 1)[0])
    checks = [
        _comparison("energy-norm convergence slope", energy_slope, truth["expected_slope"], 0.12),
        {**_comparison("L2 convergence slope", l2_slope, 2.0, 0.15), "exact_source": "Q1 theory"},
    ]
    return {
        "id": "V3", "name": "manufactured 2D solution", "checks": checks,
        "mesh_history": [
            {"elements_per_side": int(n), "h": float(1/n), "l2_error": float(e[0]), "energy_error": float(e[1])}
            for n, e in zip(meshes, errors)
        ],
    }


def verify_v4_v5(model: HeatSinkModel) -> list[dict]:
    design = model.initial_design()
    balance_checks = []
    for case in model.config.load_cases:
        for nonlinear in (False, True):
            solved = model.solve(design, case, nonlinear=nonlinear)
            relative = abs(solved.energy_imbalance_w) / case.power_w
            balance_checks.append({
                "quantity": f"{case.name} {'nonlinear' if nonlinear else 'linear'} energy balance",
                "computed": relative, "exact": 0.0, "absolute_error": relative,
                "relative_error": relative, "tolerance": 1.0e-8, "pass": bool(relative < 1.0e-8),
            })
    case = model.config.load_cases[0]
    asymmetric = design.copy()
    count = model.config.geometry.candidate_fins
    asymmetric[:count] = np.linspace(0.012, 0.048, count)
    asymmetric[count:] = np.linspace(0.15, 1.0, count)
    original = model.solve(asymmetric, case, nonlinear=True).temperature_k[:model.base_dofs]
    mirrored_design = np.r_[asymmetric[:count][::-1], asymmetric[count:][::-1]]
    mirrored = model.solve(mirrored_design, case, nonlinear=True).temperature_k[:model.base_dofs]
    permutation_error = float(np.max(np.abs(original.reshape(model.nz+1, model.nx+1)[:, ::-1] - mirrored.reshape(model.nz+1, model.nx+1))))
    si = line_conduction_matrix(167.0, 5.0e-5, 0.040)
    millimetres = line_conduction_matrix(0.167, 50.0, 40.0)
    unit_error = float(np.max(np.abs(si - millimetres)))
    invariance_checks = [
        _comparison("reflection/permutation max error K", permutation_error, 0.0, 2.0e-9),
        _comparison("SI/mm line-matrix max error W/K", unit_error, 0.0, 1.0e-12),
    ]
    return [
        {"id": "V4", "name": "global heat balance", "checks": balance_checks},
        {"id": "V5", "name": "invariance and units", "checks": invariance_checks},
    ]


def _v6_residual(temperature: float) -> tuple[float, float]:
    area, ambient, power, epsilon, sigma = 0.010, 298.15, 8.0, 0.80, 5.670374419e-8
    delta = temperature - ambient
    h = 5.0 * (delta / 20.0) ** 0.25
    residual = area * (h * delta + epsilon * sigma * (temperature**4 - ambient**4)) - power
    derivative = area * (1.25 * h + 4.0 * epsilon * sigma * temperature**3)
    return float(residual), float(derivative)


def verify_v6(truth: dict) -> dict:
    temperature = 350.0
    iterates = []
    residuals = []
    for _ in range(3):
        residual, derivative = _v6_residual(temperature)
        temperature -= residual / derivative
        iterates.append(temperature)
        residuals.append(abs(_v6_residual(temperature)[0]))
    checks = [
        _comparison("equilibrium temperature", iterates[-1], truth["equilibrium_temperature_k"], 5.0e-3)
    ]
    for index, (computed, submitted) in enumerate(zip(iterates, truth["newton_iterates_k"]), start=1):
        # The students confirmed these calculator values were rounded to about
        # 0.002 K; retain both numbers in the evidence rather than replacing truth.
        checks.append(_comparison(f"Newton T{index}", computed, submitted, 2.0e-3))
    numerical_tangent = (_v6_residual(iterates[-1] + 1.0e-4)[0] - _v6_residual(iterates[-1] - 1.0e-4)[0]) / 2.0e-4
    analytic_tangent = _v6_residual(iterates[-1])[1]
    checks.append(_comparison("analytic tangent vs finite difference", analytic_tangent, numerical_tangent, 1.0e-9))
    quadratic_ratios = [residuals[i + 1] / residuals[i] ** 2 for i in range(len(residuals) - 1)]
    return {
        "id": "V6", "name": "nonlinear scalar Newton benchmark", "checks": checks,
        "computed_iterates_k": iterates, "residual_sequence_w": residuals,
        "residual_quadratic_ratios": quadratic_ratios,
        "computed_derivative_w_per_k": analytic_tangent,
        "submitted_derivative_w_per_k": truth.get("residual_derivative_w_per_k"),
    }


def load_truth(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def benchmark_verification(model: HeatSinkModel, truth: dict) -> dict:
    groups = [verify_v1(truth["v1"]), verify_v2(truth["v2"]), verify_v3(truth["v3"])]
    groups.extend(verify_v4_v5(model))
    groups.append(verify_v6(truth["v6"]))
    checks = [check for group in groups for check in group["checks"]]
    return {
        "status": "passed" if all(check["pass"] for check in checks) else "failed",
        "student_attestation": truth["student_attestation"],
        "groups": groups,
        "passed_checks": sum(bool(check["pass"]) for check in checks),
        "total_checks": len(checks),
    }


def write_evidence(evidence: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Verification evidence",
        "",
        f"Status: **{evidence['status'].upper()}** "
        f"({evidence['passed_checks']}/{evidence['total_checks']} checks passed).",
        "",
        "Regenerate from the repository root:",
        "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe -m Project4.heatsink.benchmark_verification --config Project4\\config.yaml",
        "```",
        "",
        "| ID | Quantity | Computed | Submitted/exact | Abs. error | Tolerance | Pass |",
        "|---|---|---:|---:|---:|---:|:---:|",
    ]
    for group in evidence["groups"]:
        for check in group["checks"]:
            lines.append(
                f"| {group['id']} | {check['quantity']} | {check['computed']:.10g} | "
                f"{check['exact']:.10g} | {check['absolute_error']:.3g} | {check['tolerance']:.3g} | "
                f"{'PASS' if check['pass'] else 'FAIL'} |"
            )
    (directory / "verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Regenerate V1--V6 evidence without running optimization."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="Project4/config.yaml")
    parser.add_argument("--truth")
    parser.add_argument("--output")
    arguments = parser.parse_args(argv)

    config_path = Path(arguments.config).resolve()
    project_directory = config_path.parent
    config = load_config(config_path)
    truth_path = (
        Path(arguments.truth).resolve()
        if arguments.truth
        else project_directory / "tests" / "benchmark_truth.yaml"
    )
    output_directory = (
        Path(arguments.output).resolve()
        if arguments.output
        else project_directory / "results" / "verification"
    )
    evidence = benchmark_verification(HeatSinkModel(config), load_truth(truth_path))
    write_evidence(evidence, output_directory)
    print(
        f"V1-V6 verification {evidence['status']}: "
        f"{evidence['passed_checks']}/{evidence['total_checks']} checks passed; "
        f"evidence written to {output_directory}"
    )
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

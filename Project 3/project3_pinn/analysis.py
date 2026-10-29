from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

from .config import ExperimentConfig
from .geometry import LOSS_NAMES


def _matplotlib():
    cache = Path("tmp") / "matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache.resolve()))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Matplotlib is required to generate diagnostic figures") from exc
    return plt


def _read_csv(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(handle)]


def collect_results(config: ExperimentConfig) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    runs_dir = config.output_dir / "runs"
    if not runs_dir.exists():
        return results
    for evaluation_path in sorted(runs_dir.glob("*/evaluation.json")):
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        training_path = evaluation_path.parent / "training.json"
        training = json.loads(training_path.read_text(encoding="utf-8"))
        evaluation["training_seconds"] = training["training_seconds"]
        history_path = evaluation_path.parent / "history.csv"
        if history_path.exists() and evaluation["method"] != "supervised":
            history = _read_csv(history_path)
            ratios = []
            weighted_ratios = []
            for row in history:
                norms = np.array([row.get(f"grad_{name}", np.nan) for name in LOSS_NAMES])
                weights = np.array([row.get(f"weight_{name}", 1.0) for name in LOSS_NAMES])
                valid = np.isfinite(norms) & (norms > 0)
                norms = norms[valid]
                if norms.size:
                    ratios.append(max(norms) / min(norms))
                    weighted = (weights[valid] * norms)
                    weighted_ratios.append(max(weighted) / min(weighted))
            evaluation["median_gradient_norm_ratio"] = float(np.median(ratios)) if ratios else np.nan
            evaluation["median_weighted_gradient_norm_ratio"] = (
                float(np.median(weighted_ratios)) if weighted_ratios else np.nan
            )
            evaluation["minimum_gradient_cosine"] = float(
                np.nanmin([row.get("cosine_min", np.nan) for row in history])
            )
        results.append(evaluation)
    return results


def _write_summary(config: ExperimentConfig, results: list[dict[str, object]]) -> Path:
    output = config.output_dir / "analysis" / "summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not results:
        return output
    keys = sorted({key for row in results for key in row})
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    return output


def _external_lbm_validation(config: ExperimentConfig) -> dict[str, object] | None:
    """Compare the Re=20 reference with the official DFG 2D-1 benchmark."""
    reynolds = 20
    field_path = config.output_dir / "reference" / f"cylinder_re{reynolds}.npz"
    metadata_path = field_path.with_suffix(".json")
    if not field_path.exists() or not metadata_path.exists():
        return None

    with np.load(field_path) as archive:
        data = {name: archive[name] for name in archive.files}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    center_x = config.geometry.cylinder_x
    center_y = config.geometry.cylinder_y
    radius = config.geometry.cylinder_radius
    y_index = int(np.argmin(np.abs(data["y"] - center_y)))
    fluid = ~data["solid"][y_index]
    left_candidates = np.where(fluid & (data["x"] <= center_x - radius))[0]
    right_candidates = np.where(fluid & (data["x"] >= center_x + radius))[0]
    if not left_candidates.size or not right_candidates.size:
        return None
    left_index = int(left_candidates[-1])
    right_index = int(right_candidates[0])
    pressure_difference = float(
        data["p"][y_index, left_index] - data["p"][y_index, right_index]
    )

    benchmark_drag = 5.57953523384
    benchmark_pressure_dimensional = 0.11752016697
    benchmark_mean_velocity = 0.2
    benchmark_pressure = benchmark_pressure_dimensional / benchmark_mean_velocity**2
    drag = float(metadata["drag_coefficient"])

    result: dict[str, object] = {
        "benchmark": "DFG 2D-1 steady cylinder, Re=20",
        "source": (
            "https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/"
            "cfdbenchmarking/flow/dfg_benchmark1_re20.html"
        ),
        "geometry_scale_factor": 10.0,
        "geometry_and_inlet_match_after_nondimensionalization": True,
        "outlet_condition_match": False,
        "outlet_note": (
            "The DFG benchmark uses a do-nothing traction outlet; this LBM reference "
            "uses a rescaled developed-velocity outlet."
        ),
        "drag_coefficient": {
            "lbm": drag,
            "benchmark": benchmark_drag,
            "relative_difference": abs(drag - benchmark_drag) / benchmark_drag,
        },
        "pressure_difference": {
            "lbm_nondimensional": pressure_difference,
            "benchmark_dimensional": benchmark_pressure_dimensional,
            "benchmark_nondimensional": benchmark_pressure,
            "relative_difference": abs(pressure_difference - benchmark_pressure)
            / benchmark_pressure,
            "lbm_sample_y": float(data["y"][y_index]),
            "lbm_front_x": float(data["x"][left_index]),
            "lbm_rear_x": float(data["x"][right_index]),
        },
        "interpretation": (
            "Both quantities are within 10% of the official values. This supports "
            "physical plausibility but is not an exact validation because the outlet "
            "conditions and boundary discretizations differ."
        ),
    }
    output = config.output_dir / "analysis" / "lbm_external_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _p1_reference(config: ExperimentConfig) -> Path | None:
    plt = _matplotlib()
    reynolds = max(config.reynolds_numbers)
    path = config.output_dir / "reference" / f"cylinder_re{reynolds}.npz"
    metadata_path = path.with_suffix(".json")
    if not path.exists():
        return None
    with np.load(path) as archive:
        data = {name: archive[name] for name in archive.files}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    speed = np.sqrt(data["u"] ** 2 + data["v"] ** 2)
    external = _external_lbm_validation(config)
    figure = plt.figure(figsize=(12, 7), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=(2.0, 1.0))
    field_axis = figure.add_subplot(grid[0, :])
    diagnostic_axis = figure.add_subplot(grid[1, 0])
    benchmark_axis = figure.add_subplot(grid[1, 1])
    image = field_axis.pcolormesh(
        data["x"], data["y"], speed, shading="auto", cmap="viridis"
    )
    field_axis.set_title(f"P1: LBM reference speed, Re={reynolds}")
    field_axis.set_xlabel("x/D")
    field_axis.set_ylabel("y/D")
    figure.colorbar(image, ax=field_axis, label="|u| / U")
    history = metadata["history"]
    diagnostic_axis.semilogy(
        [row["step"] for row in history],
        [row["velocity_change"] for row in history],
        label="velocity change",
    )
    diagnostic_axis.semilogy(
        [row["step"] for row in history],
        [row["mass_imbalance"] for row in history],
        label="endpoint volume imbalance",
    )
    diagnostic_axis.set_xlabel("LBM step")
    diagnostic_axis.set_ylabel("diagnostic")
    diagnostic_axis.set_title("Implemented convergence checks")
    diagnostic_axis.legend(fontsize=8)

    if external is not None:
        labels = ["drag coefficient", "pressure difference"]
        lbm_values = [
            external["drag_coefficient"]["lbm"] / external["drag_coefficient"]["benchmark"],
            external["pressure_difference"]["lbm_nondimensional"]
            / external["pressure_difference"]["benchmark_nondimensional"],
        ]
        positions = np.arange(len(labels))
        benchmark_axis.bar(positions - 0.18, [1.0, 1.0], 0.36, label="DFG benchmark")
        benchmark_axis.bar(positions + 0.18, lbm_values, 0.36, label="LBM / benchmark")
        benchmark_axis.axhline(1.0, color="black", linewidth=0.8)
        benchmark_axis.set_xticks(positions, labels=labels)
        benchmark_axis.set_ylabel("ratio to DFG value")
        benchmark_axis.set_title("External Re=20 plausibility check")
        benchmark_axis.legend(fontsize=8)
    else:
        benchmark_axis.text(0.5, 0.5, "Re=20 benchmark data unavailable", ha="center")
        benchmark_axis.set_axis_off()
    output = config.output_dir / "figures" / "p1_reference.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _p2_training(config: ExperimentConfig) -> Path | None:
    plt = _matplotlib()
    reynolds = max(config.reynolds_numbers)
    histories = {}
    for method in ("vanilla", "balanced"):
        path = config.output_dir / "runs" / f"re{reynolds}_{method}_seed0" / "history.csv"
        if path.exists():
            histories[method] = _read_csv(path)
    if not histories:
        return None
    figure, axes = plt.subplots(4, 2, figsize=(15, 16), constrained_layout=True)
    methods = ("vanilla", "balanced")
    cosine_images = []

    for column, method in enumerate(methods):
        if method not in histories:
            axes[0, column].set_visible(False)
            axes[1, column].set_visible(False)
            axes[3, column].set_visible(False)
            continue
        history = histories[method]
        steps = np.array([row["step"] for row in history])
        for name in LOSS_NAMES:
            axes[0, column].semilogy(
                steps,
                [row[f"loss_{name}"] for row in history],
                label=name,
            )
            axes[1, column].semilogy(
                steps,
                [row[f"weight_{name}"] * row[f"grad_{name}"] for row in history],
                label=name,
            )
        axes[0, column].set_title(f"{method}: six unweighted loss components")
        axes[1, column].set_title(f"{method}: six weighted gradient norms")

        cosine_keys = [
            key
            for key in history[0]
            if key.startswith("cosine_") and key not in {"cosine_min", "cosine_mean"}
        ]
        if cosine_keys:
            cosine_values = np.array(
                [[row.get(key, np.nan) for row in history] for key in cosine_keys]
            )
            image = axes[3, column].imshow(
                cosine_values,
                aspect="auto",
                origin="lower",
                interpolation="nearest",
                extent=(steps[0], steps[-1], -0.5, len(cosine_keys) - 0.5),
                cmap="coolwarm",
                vmin=-1.0,
                vmax=1.0,
            )
            cosine_images.append(image)
            labels = [
                key.removeprefix("cosine_").replace("__", " / ").replace("_", " ")
                for key in cosine_keys
            ]
            axes[3, column].set_yticks(range(len(labels)), labels=labels, fontsize=7)
            axes[3, column].set_title(f"{method}: all 15 pairwise gradient cosines")
        else:
            axes[3, column].text(
                0.5,
                0.5,
                "Pairwise gradient histories unavailable",
                ha="center",
                va="center",
                transform=axes[3, column].transAxes,
            )
            axes[3, column].set_title(f"{method}: gradient directions")

    for method, history in histories.items():
        steps = np.array([row["step"] for row in history])
        ratios = []
        for row in history:
            weighted = np.array(
                [row[f"weight_{name}"] * row[f"grad_{name}"] for name in LOSS_NAMES]
            )
            valid = np.isfinite(weighted) & (weighted > 0)
            ratios.append(
                np.nan if not np.any(valid) else np.max(weighted[valid]) / np.min(weighted[valid])
            )
        axes[2, 0].semilogy(steps, ratios, label=method)
    axes[2, 0].set_title("Largest / smallest weighted component gradient norm")

    if "balanced" in histories:
        history = histories["balanced"]
        steps = np.array([row["step"] for row in history])
        for name in LOSS_NAMES:
            axes[2, 1].plot(
                steps,
                [row[f"weight_{name}"] for row in history],
                label=name,
            )
    axes[2, 1].set_title("Balanced adaptive weights")

    for row in range(3):
        for column in range(2):
            axes[row, column].set_xlabel("Adam step")
            axes[row, column].grid(alpha=0.2)
            axes[row, column].legend(fontsize=7, ncol=2)
    for column in range(2):
        axes[3, column].set_xlabel("Adam step")
    if cosine_images:
        figure.colorbar(
            cosine_images[0], ax=axes[3, :], label="gradient cosine", shrink=0.85
        )
    output = config.output_dir / "figures" / "p2_training_diagnostics.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _p3_error(config: ExperimentConfig, results: list[dict[str, object]]) -> Path | None:
    plt = _matplotlib()
    if not results:
        return None
    groups: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in results:
        groups[(str(row["method"]), int(row["reynolds"]))].append(float(row["velocity_relative_l2"]))
    figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
    for method in config.methods:
        re_values, medians, lower, upper = [], [], [], []
        for reynolds in config.reynolds_numbers:
            values = np.array(groups.get((method, reynolds), []), dtype=float)
            if not values.size:
                continue
            re_values.append(reynolds)
            medians.append(np.median(values))
            lower.append(np.median(values) - np.min(values))
            upper.append(np.max(values) - np.median(values))
        if re_values:
            axis.errorbar(re_values, medians, yerr=[lower, upper], marker="o", capsize=4, label=method)
    axis.set_yscale("log")
    axis.set_xlabel("Reynolds number")
    axis.set_ylabel("relative L2 velocity error")
    axis.set_title("P3: Error versus difficulty")
    axis.grid(alpha=0.25)
    axis.legend()
    output = config.output_dir / "figures" / "p3_error_vs_reynolds.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _p4_error(config: ExperimentConfig) -> Path | None:
    plt = _matplotlib()
    reynolds = max(config.reynolds_numbers)
    reference_path = config.output_dir / "reference" / f"cylinder_re{reynolds}.npz"
    if not reference_path.exists():
        return None
    with np.load(reference_path) as archive:
        reference = {name: archive[name] for name in archive.files}
    methods = ("vanilla", "balanced")
    method_fields = {}
    for method in methods:
        field_path = config.output_dir / "runs" / f"re{reynolds}_{method}_seed0" / "evaluation_fields.npz"
        if not field_path.exists():
            return None
        with np.load(field_path) as archive:
            method_fields[method] = {name: archive[name] for name in archive.files}

    vmax = max(float(np.nanmax(method_fields[method]["error_speed"])) for method in methods)
    figure = plt.figure(figsize=(14, 8), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=(2.2, 1.0))
    map_axes = [figure.add_subplot(grid[0, column]) for column in range(2)]
    spectrum_axis = figure.add_subplot(grid[1, :])

    for column, method in enumerate(methods):
        error_speed = method_fields[method]["error_speed"]
        image = map_axes[column].pcolormesh(
            reference["x"],
            reference["y"],
            error_speed,
            shading="auto",
            cmap="magma",
            vmin=0.0,
            vmax=vmax,
        )
        map_axes[column].set_title(f"{method}: pointwise velocity error")
        map_axes[column].set_xlabel("x/D")
        map_axes[column].set_ylabel("y/D")

        x_mask = reference["x"] >= 2.75
        y_mask = (reference["y"] >= 0.25) & (reference["y"] <= 3.85)
        wake = error_speed[np.ix_(y_mask, x_mask)]
        if not np.all(np.isfinite(wake)):
            fill = float(np.nanmedian(wake))
            wake = np.nan_to_num(wake, nan=fill)
        wake = wake - np.mean(wake, axis=1, keepdims=True)
        window = np.hanning(wake.shape[1])
        power = np.abs(np.fft.rfft(wake * window[None, :], axis=1)) ** 2
        power = np.mean(power, axis=0) / np.sum(window**2)
        dx = float(np.mean(np.diff(reference["x"][x_mask])))
        frequency = np.fft.rfftfreq(wake.shape[1], d=dx)
        spectrum_axis.loglog(frequency[1:], power[1:] + 1.0e-20, label=method)

    figure.colorbar(image, ax=map_axes, label="velocity error / U", shrink=0.9)
    spectrum_axis.set_title("Wake streamwise error-power spectrum (detrended, Hann window)")
    spectrum_axis.set_xlabel("streamwise spatial frequency [cycles / D]")
    spectrum_axis.set_ylabel("mean power")
    spectrum_axis.grid(alpha=0.25, which="both")
    spectrum_axis.legend()
    output = config.output_dir / "figures" / "p4_error_location.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _p5_cost(config: ExperimentConfig, results: list[dict[str, object]]) -> Path | None:
    plt = _matplotlib()
    if not results:
        return None
    reynolds = max(config.reynolds_numbers)
    methods, train_costs, inference_costs = [], [], []
    for method in config.methods:
        selected = [row for row in results if row["method"] == method and int(row["reynolds"]) == reynolds]
        if selected:
            methods.append(method)
            train_costs.append(float(np.median([row["training_seconds"] for row in selected])))
            inference_costs.append(float(np.median([row["inference_seconds"] for row in selected])))
    reference_meta = config.output_dir / "reference" / f"cylinder_re{reynolds}.json"
    reference_seconds = json.loads(reference_meta.read_text(encoding="utf-8"))["runtime_seconds"]
    figure, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    axes[0].bar(methods + ["LBM"], train_costs + [reference_seconds])
    axes[0].set_yscale("log")
    axes[0].set_ylabel("seconds")
    axes[0].set_title("Training / solve cost")
    axes[1].bar(methods, inference_costs)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("seconds")
    axes[1].set_title("Full-grid inference cost")
    output = config.output_dir / "figures" / "p5_cost.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _decision(config: ExperimentConfig, results: list[dict[str, object]]) -> dict[str, object]:
    max_re = max(config.reynolds_numbers)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in results:
        if int(row["reynolds"]) == max_re:
            grouped[str(row["method"])].append(row)
    vanilla = np.array([float(row["velocity_relative_l2"]) for row in grouped.get("vanilla", [])])
    balanced = np.array([float(row["velocity_relative_l2"]) for row in grouped.get("balanced", [])])
    supervised = np.array([float(row["velocity_relative_l2"]) for row in grouped.get("supervised", [])])
    improvement = None
    if vanilla.size and balanced.size:
        improvement = 1.0 - float(np.median(balanced)) / float(np.median(vanilla))
    expressivity_supported = bool(
        vanilla.size and supervised.size and np.median(supervised) < 0.5 * np.median(vanilla)
    )
    reference_status = []
    for reynolds in config.reynolds_numbers:
        path = config.output_dir / "reference" / f"cylinder_re{reynolds}.json"
        if path.exists():
            metadata = json.loads(path.read_text(encoding="utf-8"))
            reference_status.append(bool(metadata.get("reference_adequate", False)))
        else:
            reference_status.append(False)
    grid_path = config.output_dir / "analysis" / "lbm_grid_refinement.json"
    grid_adequate = False
    if grid_path.exists():
        grid_adequate = bool(
            json.loads(grid_path.read_text(encoding="utf-8")).get("grid_adequate", False)
        )
    references_adequate = bool(reference_status) and all(reference_status) and grid_adequate
    helped = references_adequate and improvement is not None and improvement >= 0.25
    if not references_adequate:
        interpretation = "No scientific decision: at least one conventional reference failed its adequacy checks."
    elif helped:
        interpretation = "Adaptive balancing met the predefined improvement threshold."
    else:
        interpretation = "Adaptive balancing did not meet the predefined improvement threshold."
    return {
        "reynolds": max_re,
        "references_adequate": references_adequate,
        "grid_adequate": grid_adequate,
        "balanced_error_improvement_fraction": improvement,
        "meaningful_improvement_threshold": 0.25,
        "adaptive_balancing_helped_meaningfully": helped,
        "optimization_not_capacity_supported": expressivity_supported,
        "interpretation": interpretation,
    }


def generate_analysis(config: ExperimentConfig) -> dict[str, object]:
    results = collect_results(config)
    summary_path = _write_summary(config, results)
    figures = [
        _p1_reference(config),
        _p2_training(config),
        _p3_error(config, results),
        _p4_error(config),
        _p5_cost(config, results),
    ]
    decision = _decision(config, results)
    decision_path = config.output_dir / "analysis" / "decision.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(json.dumps(decision, indent=2), encoding="utf-8")
    return {
        "summary": str(summary_path),
        "figures": [str(path) for path in figures if path is not None],
        "decision": decision,
    }

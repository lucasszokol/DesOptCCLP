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
    figure, axes = plt.subplots(2, 1, figsize=(10, 6), constrained_layout=True)
    image = axes[0].pcolormesh(data["x"], data["y"], speed, shading="auto", cmap="viridis")
    axes[0].set_title(f"P1: LBM reference speed, Re={reynolds}")
    axes[0].set_xlabel("x/D")
    axes[0].set_ylabel("y/D")
    figure.colorbar(image, ax=axes[0], label="|u| / U")
    history = metadata["history"]
    axes[1].semilogy([row["step"] for row in history], [row["velocity_change"] for row in history], label="velocity change")
    axes[1].semilogy([row["step"] for row in history], [row["mass_imbalance"] for row in history], label="mass imbalance")
    axes[1].set_xlabel("LBM step")
    axes[1].set_ylabel("diagnostic")
    axes[1].legend()
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
    figure, axes = plt.subplots(3, 2, figsize=(12, 11), constrained_layout=True)
    for method, history in histories.items():
        steps = [row["step"] for row in history]
        axes[0, 0].semilogy(steps, [row["total"] for row in history], label=method)
        ratios = []
        for row in history:
            norms = np.array([row[f"grad_{name}"] for name in LOSS_NAMES])
            weights = np.array([row.get(f"weight_{name}", 1.0) for name in LOSS_NAMES])
            finite = norms[np.isfinite(norms) & (norms > 0)]
            valid = np.isfinite(norms) & (norms > 0)
            weighted = norms[valid] * weights[valid]
            ratios.append(np.nan if not finite.size else np.max(weighted) / np.min(weighted))
        axes[0, 1].semilogy(steps, ratios, label=method)
    axes[0, 0].set_title("Total weighted loss")
    axes[0, 1].set_title("Largest / smallest weighted component gradient norm")
    for name in LOSS_NAMES:
        if "vanilla" in histories:
            history = histories["vanilla"]
            axes[1, 0].semilogy(
                [row["step"] for row in history],
                [row[f"loss_{name}"] for row in history],
                label=name,
            )
        if "balanced" in histories:
            history = histories["balanced"]
            axes[1, 1].plot(
                [row["step"] for row in history],
                [row[f"weight_{name}"] for row in history],
                label=name,
            )
    axes[1, 0].set_title("Vanilla loss components")
    axes[1, 1].set_title("Balanced adaptive weights")
    if "vanilla" in histories:
        history = histories["vanilla"]
        steps = [row["step"] for row in history]
        for name in LOSS_NAMES:
            axes[2, 0].semilogy(steps, [row[f"grad_{name}"] for row in history], label=name)
        axes[2, 0].set_title("Vanilla component gradient norms")
    for method, history in histories.items():
        steps = [row["step"] for row in history]
        axes[2, 1].plot(steps, [row["cosine_min"] for row in history], label=f"{method}: minimum")
        axes[2, 1].plot(steps, [row["cosine_mean"] for row in history], linestyle="--", label=f"{method}: mean")
    axes[2, 1].axhline(0.0, color="black", linewidth=0.8)
    axes[2, 1].set_title("Pairwise gradient alignment")
    for axis in axes.flat:
        axis.set_xlabel("Adam step")
        axis.legend(fontsize=7)
        axis.grid(alpha=0.2)
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
    figure, axes = plt.subplots(2, 2, figsize=(12, 6), constrained_layout=True)
    found = False
    for column, method in enumerate(("vanilla", "balanced")):
        field_path = config.output_dir / "runs" / f"re{reynolds}_{method}_seed0" / "evaluation_fields.npz"
        if not field_path.exists():
            continue
        found = True
        with np.load(field_path) as archive:
            fields = {name: archive[name] for name in archive.files}
        image = axes[0, column].pcolormesh(
            reference["x"], reference["y"], fields["error_speed"], shading="auto", cmap="magma"
        )
        axes[0, column].set_title(f"{method}: pointwise velocity error")
        figure.colorbar(image, ax=axes[0, column])
        wake = fields["error_speed"][:, reference["x"] >= 2.5]
        wake = np.nan_to_num(wake, nan=0.0)
        spectrum = np.abs(np.fft.rfft2(wake))
        radial = np.mean(spectrum, axis=0)
        axes[1, column].loglog(np.arange(1, radial.size), radial[1:] + 1.0e-16)
        axes[1, column].set_title(f"{method}: wake error spectrum")
        axes[1, column].set_xlabel("streamwise frequency index")
    if not found:
        plt.close(figure)
        return None
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

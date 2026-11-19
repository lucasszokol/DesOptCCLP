"""Generate presentation figures exclusively from the canonical results JSON."""

from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def generate_figures(results_path: Path, output_directory: Path) -> list[Path]:
    data = json.loads(Path(results_path).read_text(encoding="utf-8"))
    if data.get("status") != "final":
        raise ValueError("Presentation figures require final validated results")
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        path = output_directory / name
        fig.savefig(path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)

    designs = data["designs"]
    selected = [designs["initial"], designs["linear_fixed"], designs["nonlinear_fixed"], data["uncertainty"]["design"]]
    labels = ["Initial\n(infeasible)", "Linear\nfixed topology", "Nonlinear\nfixed topology", "Uncertainty\nscenarios"]
    fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
    bars = ax.bar(labels, [d["mass_kg"] * 1000 for d in selected], color=["#9aa6b2", "#76a4ce", "#25639b", "#163f6b"])
    ax.bar_label(bars, fmt="%.1f g", padding=4)
    ax.set(ylabel="Heat-sink mass (g)", title="Mass comparison: feasible designs versus starting geometry")
    ax.set_ylim(0, max(d["mass_kg"] * 1000 for d in selected) * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "mass-comparison.png")

    fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
    for check in data["gradient_checks"]:
        rows = check["rows"]
        ax.loglog([r["step"] for r in rows], [max(r["absolute_error"], 1e-16) for r in rows],
                  marker=".", label=f"{check['load_case']} / {check['variable_family']} (slope {check['taylor_slope']:.2f})")
    ax.set(xlabel="Dimensionless step", ylabel="First-order Taylor remainder", title="Adjoint Taylor checks")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=9)
    save(fig, "taylor-checks.png")

    u = data["uncertainty"]
    baseline = u["baseline_design"]["load_cases"]
    robust = u["design"]["load_cases"]
    names = [case["name"].replace("_", " ") for case in robust]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    ax.bar(x - .19, [100 * c["scaled_constraint"] for c in baseline], width=.38, label="Nominal optimum", color="#cf6a33")
    ax.bar(x + .19, [100 * c["scaled_constraint"] for c in robust], width=.38, label="Scenario optimum", color="#25639b")
    ax.axhline(0, color="#222", linewidth=1)
    ax.set_xticks(x, names)
    ax.set(ylabel="KS constraint relative to limit (%)", title="Scenario robustness: positive values violate the limit")
    ax.grid(axis="y", alpha=.25)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "uncertainty-comparison.png")
    return paths

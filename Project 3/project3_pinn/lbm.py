from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from .config import ExperimentConfig


C = np.array(
    [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1], [1, 1], [-1, 1], [-1, -1], [1, -1]],
    dtype=np.int8,
)
W = np.array([4 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 9, 1 / 36, 1 / 36, 1 / 36, 1 / 36])
OPPOSITE = np.array([0, 3, 4, 1, 2, 7, 8, 5, 6])


def equilibrium(rho: np.ndarray, ux: np.ndarray, uy: np.ndarray) -> np.ndarray:
    cu = C[:, 0, None, None] * ux + C[:, 1, None, None] * uy
    usq = ux * ux + uy * uy
    return W[:, None, None] * rho * (1.0 + 3.0 * cu + 4.5 * cu * cu - 1.5 * usq)


def _macroscopic(f: np.ndarray, fluid: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rho = np.sum(f, axis=0)
    rho_safe = np.where(rho > 1.0e-12, rho, 1.0)
    ux = np.sum(f * C[:, 0, None, None], axis=0) / rho_safe
    uy = np.sum(f * C[:, 1, None, None], axis=0) / rho_safe
    ux[~fluid] = 0.0
    uy[~fluid] = 0.0
    return rho, ux, uy


def run_lbm(config: ExperimentConfig, reynolds: int, *, force: bool = False) -> Path:
    out_dir = config.output_dir / "reference"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"cylinder_re{reynolds}.npz"
    metadata_path = out_dir / f"cylinder_re{reynolds}.json"
    if output.exists() and metadata_path.exists() and not force:
        return output

    g = config.geometry
    cfg = config.lbm
    diameter_nodes = cfg.nodes_per_diameter
    nx = int(round(g.length * diameter_nodes)) + 1
    ny = int(round(g.height * diameter_nodes)) + 1
    x = np.linspace(0.0, g.length, nx)
    y = np.linspace(0.0, g.height, ny)
    xx, yy = np.meshgrid(x, y)
    cylinder = (xx - g.cylinder_x) ** 2 + (yy - g.cylinder_y) ** 2 <= g.cylinder_radius**2
    walls = np.zeros((ny, nx), dtype=bool)
    walls[0, :] = True
    walls[-1, :] = True
    solid = cylinder | walls
    fluid = ~solid

    lattice_diameter = g.cylinder_radius * 2.0 * diameter_nodes
    mean_u = cfg.lattice_mean_velocity
    viscosity = mean_u * lattice_diameter / reynolds
    tau = 0.5 + 3.0 * viscosity
    if tau <= 0.515:
        raise ValueError(f"LBM relaxation time {tau:.4f} is too close to instability")

    y_lattice = np.arange(ny, dtype=float)
    inlet_u = 6.0 * mean_u * y_lattice * (ny - 1 - y_lattice) / (ny - 1) ** 2
    inlet_u[[0, -1]] = 0.0
    ux = np.broadcast_to(inlet_u[:, None], (ny, nx)).copy()
    uy = np.zeros_like(ux)
    ux[solid] = 0.0
    rho = np.ones_like(ux)
    f = equilibrium(rho, ux, uy)

    history: list[dict[str, float]] = []
    previous = ux.copy()
    start = time.perf_counter()
    drag_force = 0.0
    converged = False
    consecutive_converged = 0

    for step in range(1, cfg.max_steps + 1):
        rho, ux, uy = _macroscopic(f, fluid)
        feq = equilibrium(rho, ux, uy)
        post = f - (f - feq) / tau
        streamed = np.empty_like(f)
        for i, (cx, cy) in enumerate(C):
            streamed[i] = np.roll(np.roll(post[i], int(cy), axis=0), int(cx), axis=1)

        drag_force = 0.0
        for i in range(1, 9):
            cx, cy = int(C[i, 0]), int(C[i, 1])
            neighbor_solid = np.roll(np.roll(solid, -cy, axis=0), -cx, axis=1) & fluid
            neighbor_cylinder = np.roll(np.roll(cylinder, -cy, axis=0), -cx, axis=1) & fluid
            streamed[OPPOSITE[i], neighbor_solid] = post[i, neighbor_solid]
            drag_force += float(np.sum(2.0 * post[i, neighbor_cylinder] * cx))

        # Zou-He velocity inlet. Unknown populations point into the domain.
        inlet_slice = slice(1, ny - 1)
        ux_in = inlet_u[inlet_slice]
        rho_in = (
            streamed[0, inlet_slice, 0]
            + streamed[2, inlet_slice, 0]
            + streamed[4, inlet_slice, 0]
            + 2.0
            * (
                streamed[3, inlet_slice, 0]
                + streamed[6, inlet_slice, 0]
                + streamed[7, inlet_slice, 0]
            )
        ) / (1.0 - ux_in)
        streamed[1, inlet_slice, 0] = streamed[3, inlet_slice, 0] + (2.0 / 3.0) * rho_in * ux_in
        streamed[5, inlet_slice, 0] = (
            streamed[7, inlet_slice, 0]
            + 0.5 * (streamed[4, inlet_slice, 0] - streamed[2, inlet_slice, 0])
            + (1.0 / 6.0) * rho_in * ux_in
        )
        streamed[8, inlet_slice, 0] = (
            streamed[6, inlet_slice, 0]
            + 0.5 * (streamed[2, inlet_slice, 0] - streamed[4, inlet_slice, 0])
            + (1.0 / 6.0) * rho_in * ux_in
        )

        # Developed-flow outlet. Preserve the penultimate-column velocity
        # shape, rescale it to the prescribed inlet volume flux, and use the
        # east-boundary Zou-He reconstruction. At convergence the scale tends
        # to one, giving an approximately zero streamwise velocity gradient.
        outlet_u = ux[inlet_slice, -2].copy()
        outlet_v = uy[inlet_slice, -2].copy()
        outlet_flux = float(np.sum(outlet_u))
        inlet_flux_target = float(np.sum(inlet_u[inlet_slice]))
        if abs(outlet_flux) > 1.0e-12:
            outlet_u *= inlet_flux_target / outlet_flux
        known = (
            streamed[0, inlet_slice, -1]
            + streamed[2, inlet_slice, -1]
            + streamed[4, inlet_slice, -1]
            + 2.0
            * (
                streamed[1, inlet_slice, -1]
                + streamed[5, inlet_slice, -1]
                + streamed[8, inlet_slice, -1]
            )
        )
        rho_out = known / (1.0 + outlet_u)
        streamed[3, inlet_slice, -1] = (
            streamed[1, inlet_slice, -1] - (2.0 / 3.0) * rho_out * outlet_u
        )
        streamed[6, inlet_slice, -1] = (
            streamed[8, inlet_slice, -1]
            + 0.5 * (streamed[4, inlet_slice, -1] - streamed[2, inlet_slice, -1])
            - (1.0 / 6.0) * rho_out * outlet_u
            + 0.5 * rho_out * outlet_v
        )
        streamed[7, inlet_slice, -1] = (
            streamed[5, inlet_slice, -1]
            + 0.5 * (streamed[2, inlet_slice, -1] - streamed[4, inlet_slice, -1])
            - (1.0 / 6.0) * rho_out * outlet_u
            - 0.5 * rho_out * outlet_v
        )
        f = streamed

        if step % cfg.check_every == 0 or step == cfg.max_steps:
            rho, ux, uy = _macroscopic(f, fluid)
            change = np.linalg.norm((ux - previous)[fluid]) / (
                np.linalg.norm(ux[fluid]) + 1.0e-12
            )
            inlet_flux = float(np.sum(ux[1:-1, 0]))
            outlet_flux = float(np.sum(ux[1:-1, -1]))
            mass_imbalance = abs(outlet_flux - inlet_flux) / (abs(inlet_flux) + 1.0e-12)
            history.append(
                {"step": step, "velocity_change": float(change), "mass_imbalance": mass_imbalance}
            )
            previous = ux.copy()
            if step >= cfg.min_steps and change < cfg.convergence_tolerance:
                consecutive_converged += 1
            else:
                consecutive_converged = 0
            if consecutive_converged >= cfg.consecutive_convergence_checks:
                converged = True
                break

    runtime = time.perf_counter() - start
    rho, ux, uy = _macroscopic(f, fluid)
    outlet_density = float(np.mean(rho[1:-1, -1]))
    u = ux / mean_u
    v = uy / mean_u
    pressure = (rho - outlet_density) / (3.0 * mean_u**2)
    u[solid] = np.nan
    v[solid] = np.nan
    pressure[solid] = np.nan

    drag_coefficient = drag_force / (0.5 * outlet_density * mean_u**2 * lattice_diameter)
    center_row = int(np.argmin(np.abs(y - g.cylinder_y)))
    behind = x > g.cylinder_x + g.cylinder_radius
    center_u = u[center_row]
    negative = np.where(behind & np.isfinite(center_u) & (center_u < 0.0))[0]
    recirculation_length = 0.0
    if negative.size:
        recirculation_length = float(x[negative[-1]] - (g.cylinder_x + g.cylinder_radius))

    np.savez_compressed(
        output,
        x=x,
        y=y,
        u=u,
        v=v,
        p=pressure,
        solid=solid,
        reynolds=np.array(reynolds),
    )
    metadata = {
        "reynolds": reynolds,
        "runtime_seconds": runtime,
        "steps": step,
        "converged": converged,
        "tau": tau,
        "mass_imbalance": history[-1]["mass_imbalance"],
        "mass_imbalance_tolerance": cfg.mass_imbalance_tolerance,
        "velocity_change": history[-1]["velocity_change"],
        "reference_adequate": bool(
            converged
            and history[-1]["mass_imbalance"] <= cfg.mass_imbalance_tolerance
        ),
        "drag_coefficient": drag_coefficient,
        "recirculation_length": recirculation_length,
        "grid": {"nx": nx, "ny": ny, "nodes_per_diameter": diameter_nodes},
        "history": history,
        "config": asdict(cfg),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return output


def generate_references(config: ExperimentConfig, *, force: bool = False) -> list[Path]:
    return [run_lbm(config, re, force=force) for re in config.reynolds_numbers]


def grid_refinement_check(
    config: ExperimentConfig, reynolds: int | None = None, *, force: bool = False
) -> Path:
    """Compare the production grid with a half-resolution LBM reference."""
    try:
        from scipy.interpolate import RegularGridInterpolator
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("SciPy is required for the grid-refinement check") from exc

    reynolds = max(config.reynolds_numbers) if reynolds is None else reynolds
    # The caller may have just forced generation of the fine reference. Reuse
    # it here; only the separate coarse reference follows the force flag.
    fine_path = run_lbm(config, reynolds, force=False)
    coarse_lbm = replace(
        config.lbm,
        nodes_per_diameter=max(6, config.lbm.nodes_per_diameter // 2),
        max_steps=max(2_000, config.lbm.max_steps // 2),
        min_steps=max(500, config.lbm.min_steps // 2),
    )
    coarse_config = replace(
        config,
        lbm=coarse_lbm,
        output_dir=config.output_dir / "grid_check" / "coarse",
        reynolds_numbers=(reynolds,),
    )
    coarse_path = run_lbm(coarse_config, reynolds, force=force)
    with np.load(fine_path) as fine, np.load(coarse_path) as coarse:
        coarse_xx, coarse_yy = np.meshgrid(coarse["x"], coarse["y"])
        points = np.column_stack((coarse_yy.ravel(), coarse_xx.ravel()))
        fine_u = RegularGridInterpolator(
            (fine["y"], fine["x"]), fine["u"], bounds_error=False, fill_value=np.nan
        )(points).reshape(coarse["u"].shape)
        fine_v = RegularGridInterpolator(
            (fine["y"], fine["x"]), fine["v"], bounds_error=False, fill_value=np.nan
        )(points).reshape(coarse["v"].shape)
        valid = (~coarse["solid"]) & np.isfinite(fine_u) & np.isfinite(fine_v)
        numerator = np.linalg.norm(
            np.column_stack((coarse["u"][valid] - fine_u[valid], coarse["v"][valid] - fine_v[valid]))
        )
        denominator = np.linalg.norm(np.column_stack((fine_u[valid], fine_v[valid]))) + 1.0e-12
        relative_difference = float(numerator / denominator)
        compared_points = int(np.sum(valid))
    result = {
        "reynolds": reynolds,
        "fine_nodes_per_diameter": config.lbm.nodes_per_diameter,
        "coarse_nodes_per_diameter": coarse_lbm.nodes_per_diameter,
        "relative_velocity_difference": relative_difference,
        "compared_points": compared_points,
        "interpretation": "Reference discretization check; this is not a PINN error metric.",
    }
    output = config.output_dir / "analysis" / "lbm_grid_refinement.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output

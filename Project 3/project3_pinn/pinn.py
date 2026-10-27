from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import random
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import numpy as np

from .config import ExperimentConfig
from .geometry import LOSS_NAMES, TrainingPoints, sample_training_points


def _torch():
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PyTorch is required for PINN training. Install requirements-project3.txt "
            "in a Python 3.11 environment."
        ) from exc
    return torch


class CylinderPINNBase:
    """Factory wrapper that delays importing PyTorch until the model is requested."""

    @staticmethod
    def build(config: ExperimentConfig):
        torch = _torch()
        nn = torch.nn
        g = config.geometry
        p = config.pinn

        class CylinderPINN(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                layers: list[nn.Module] = [nn.Linear(2, p.hidden_width), nn.Tanh()]
                for _ in range(p.hidden_layers - 1):
                    layers.extend((nn.Linear(p.hidden_width, p.hidden_width), nn.Tanh()))
                layers.append(nn.Linear(p.hidden_width, 3))
                self.network = nn.Sequential(*layers)
                self.register_buffer(
                    "lower", torch.tensor([0.0, 0.0], dtype=torch.get_default_dtype())
                )
                self.register_buffer(
                    "upper",
                    torch.tensor([g.length, g.height], dtype=torch.get_default_dtype()),
                )
                self._initialize()

            def _initialize(self) -> None:
                for module in self.modules():
                    if isinstance(module, nn.Linear):
                        nn.init.xavier_normal_(module.weight)
                        nn.init.zeros_(module.bias)

            def forward(self, xy):
                normalized = 2.0 * (xy - self.lower) / (self.upper - self.lower) - 1.0
                return self.network(normalized)

        return CylinderPINN()


def _seed_everything(seed: int) -> None:
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch = _torch()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False


def _tensor(array: np.ndarray, device, *, requires_grad: bool = False):
    torch = _torch()
    return torch.tensor(array, device=device, dtype=torch.get_default_dtype(), requires_grad=requires_grad)


def navier_stokes_residual(model, xy, reynolds: float):
    torch = _torch()
    prediction = model(xy)
    u, v, pressure = prediction[:, 0:1], prediction[:, 1:2], prediction[:, 2:3]
    grad_u = torch.autograd.grad(u.sum(), xy, create_graph=True)[0]
    grad_v = torch.autograd.grad(v.sum(), xy, create_graph=True)[0]
    grad_p = torch.autograd.grad(pressure.sum(), xy, create_graph=True)[0]
    u_x, u_y = grad_u[:, 0:1], grad_u[:, 1:2]
    v_x, v_y = grad_v[:, 0:1], grad_v[:, 1:2]
    p_x, p_y = grad_p[:, 0:1], grad_p[:, 1:2]
    u_xx = torch.autograd.grad(u_x.sum(), xy, create_graph=True)[0][:, 0:1]
    u_yy = torch.autograd.grad(u_y.sum(), xy, create_graph=True)[0][:, 1:2]
    v_xx = torch.autograd.grad(v_x.sum(), xy, create_graph=True)[0][:, 0:1]
    v_yy = torch.autograd.grad(v_y.sum(), xy, create_graph=True)[0][:, 1:2]
    continuity = u_x + v_y
    momentum_x = u * u_x + v * u_y + p_x - (u_xx + u_yy) / reynolds
    momentum_y = u * v_x + v * v_y + p_y - (v_xx + v_yy) / reynolds
    return prediction, continuity, momentum_x, momentum_y


def component_losses(model, points: dict[str, object], reynolds: float, config: ExperimentConfig):
    torch = _torch()
    mse = lambda value: torch.mean(value * value)
    _, continuity, momentum_x, momentum_y = navier_stokes_residual(
        model, points["interior"], reynolds
    )

    inlet_prediction = model(points["inlet"])
    inlet_y = points["inlet"][:, 1:2]
    target_u = 6.0 * inlet_y * (config.geometry.height - inlet_y) / config.geometry.height**2
    inlet = mse(inlet_prediction[:, 0:1] - target_u) + mse(inlet_prediction[:, 1:2])

    wall_prediction = model(points["walls"])
    walls = mse(wall_prediction[:, 0:1]) + mse(wall_prediction[:, 1:2])

    outlet_xy = points["outlet"]
    outlet_prediction = model(outlet_xy)
    outlet_u = outlet_prediction[:, 0:1]
    outlet_v = outlet_prediction[:, 1:2]
    grad_out_u = torch.autograd.grad(outlet_u.sum(), outlet_xy, create_graph=True)[0]
    grad_out_v = torch.autograd.grad(outlet_v.sum(), outlet_xy, create_graph=True)[0]
    outlet = (
        mse(outlet_prediction[:, 2:3])
        + mse(grad_out_u[:, 0:1])
        + mse(grad_out_v[:, 0:1])
    )
    return {
        "continuity": mse(continuity),
        "momentum_x": mse(momentum_x),
        "momentum_y": mse(momentum_y),
        "inlet": inlet,
        "walls": walls,
        "outlet": outlet,
    }


def _flatten_gradients(loss, parameters: Iterable[object]):
    torch = _torch()
    params = tuple(parameters)
    gradients = torch.autograd.grad(
        loss, params, retain_graph=True, allow_unused=True, create_graph=False
    )
    flat = []
    for parameter, gradient in zip(params, gradients):
        flat.append(torch.zeros_like(parameter).reshape(-1) if gradient is None else gradient.reshape(-1))
    return torch.cat(flat)


def gradient_diagnostics(
    losses: dict[str, object], model
) -> tuple[dict[str, float], dict[str, float]]:
    torch = _torch()
    vectors = {name: _flatten_gradients(losses[name], model.parameters()) for name in LOSS_NAMES}
    norms = {name: float(torch.linalg.vector_norm(vector).detach().cpu()) for name, vector in vectors.items()}
    cosines: dict[str, float] = {}
    for index, first in enumerate(LOSS_NAMES):
        for second in LOSS_NAMES[index + 1 :]:
            denominator = torch.linalg.vector_norm(vectors[first]) * torch.linalg.vector_norm(vectors[second])
            if float(denominator.detach().cpu()) > 1.0e-20:
                value = torch.dot(vectors[first], vectors[second]) / denominator
                cosines[f"{first}__{second}"] = float(value.detach().cpu())
    return norms, cosines


def _bounded_mean_one(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    """Project positive relative weights onto bounds while preserving mean one."""
    if not lower <= 1.0 <= upper:
        raise ValueError("Adaptive-weight bounds must contain one")
    values = np.maximum(np.asarray(values, dtype=float), 1.0e-12)
    lo, hi = 0.0, 1.0
    while np.mean(np.clip(hi * values, lower, upper)) < 1.0:
        hi *= 2.0
    for _ in range(100):
        scale = 0.5 * (lo + hi)
        if np.mean(np.clip(scale * values, lower, upper)) < 1.0:
            lo = scale
        else:
            hi = scale
    return np.clip(0.5 * (lo + hi) * values, lower, upper)


def update_adaptive_weights(
    weights: dict[str, float],
    norms: dict[str, float],
    config: ExperimentConfig,
) -> dict[str, float]:
    values = np.array([max(norms[name], 1.0e-12) for name in LOSS_NAMES], dtype=float)
    target = float(np.mean(values)) / values
    target = _bounded_mean_one(target, config.pinn.min_weight, config.pinn.max_weight)
    old = np.array([weights[name] for name in LOSS_NAMES], dtype=float)
    updated = config.pinn.weight_ema * old + (1.0 - config.pinn.weight_ema) * target
    updated = _bounded_mean_one(updated, config.pinn.min_weight, config.pinn.max_weight)
    return dict(zip(LOSS_NAMES, updated.tolist()))


def _device():
    torch = _torch()
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _prepare_points(points: TrainingPoints, device) -> dict[str, object]:
    return {
        "interior": _tensor(points.interior, device, requires_grad=True),
        "inlet": _tensor(points.inlet, device),
        "walls": _tensor(points.walls, device),
        "outlet": _tensor(points.outlet, device, requires_grad=True),
    }


def _sample_batch(pool, batch_size: int, generator):
    torch = _torch()
    if batch_size >= pool.shape[0]:
        return pool.detach().clone().requires_grad_(True)
    indices = torch.randint(pool.shape[0], (batch_size,), generator=generator, device=pool.device)
    return pool[indices].detach().clone().requires_grad_(True)


def _write_history(path: Path, history: list[dict[str, float]]) -> None:
    if not history:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)


def _load_reference_samples(config: ExperimentConfig, reynolds: int, seed: int):
    reference_path = config.output_dir / "reference" / f"cylinder_re{reynolds}.npz"
    if not reference_path.exists():
        raise FileNotFoundError(f"Generate the reference first: {reference_path}")
    data = np.load(reference_path)
    xx, yy = np.meshgrid(data["x"], data["y"])
    mask = ~data["solid"] & np.isfinite(data["u"]) & np.isfinite(data["v"])
    inputs = np.column_stack((xx[mask], yy[mask])).astype(np.float32)
    outputs = np.column_stack((data["u"][mask], data["v"][mask], data["p"][mask])).astype(np.float32)
    rng = np.random.default_rng(seed)
    count = min(config.pinn.supervised_points, inputs.shape[0])
    indices = rng.choice(inputs.shape[0], size=count, replace=False)
    return inputs[indices], outputs[indices]


def _train_model_impl(
    config: ExperimentConfig,
    reynolds: int,
    seed: int,
    method: str,
    *,
    force: bool = False,
) -> Path:
    if method not in {"vanilla", "balanced", "supervised"}:
        raise ValueError(f"Unknown method: {method}")
    torch = _torch()
    torch.set_default_dtype(torch.float64 if config.pinn.dtype == "float64" else torch.float32)
    _seed_everything(seed)
    device = _device()
    run_dir = config.output_dir / "runs" / f"re{reynolds}_{method}_seed{seed}"
    checkpoint_path = run_dir / "model.pt"
    if checkpoint_path.exists() and not force:
        return checkpoint_path
    run_dir.mkdir(parents=True, exist_ok=True)

    model = CylinderPINNBase.build(config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.pinn.adam_learning_rate)
    weights = {name: 1.0 for name in LOSS_NAMES}
    history: list[dict[str, float]] = []
    generator = torch.Generator(device=device)
    generator.manual_seed(seed + 31_337)
    progress_path = run_dir / "in_progress.pt"
    start_step = 0
    elapsed_before_resume = 0.0
    adam_complete = False
    if force and progress_path.exists():
        progress_path.unlink()
    if progress_path.exists() and not force:
        progress = torch.load(progress_path, map_location=device, weights_only=False)
        if progress.get("method") != method or int(progress.get("reynolds")) != reynolds:
            raise ValueError(f"Incompatible progress checkpoint: {progress_path}")
        model.load_state_dict(progress["state_dict"])
        optimizer.load_state_dict(progress["optimizer_state_dict"])
        weights = progress["weights"]
        history = progress["history"]
        start_step = int(progress["step"])
        elapsed_before_resume = float(progress.get("elapsed_seconds", 0.0))
        adam_complete = bool(progress.get("adam_complete", False))
        generator.set_state(progress["generator_state"])
    start = time.perf_counter()

    def save_progress(step: int, *, complete: bool = False) -> None:
        torch.save(
            {
                "state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "weights": weights,
                "history": history,
                "step": step,
                "adam_complete": complete,
                "generator_state": generator.get_state(),
                "elapsed_seconds": elapsed_before_resume + time.perf_counter() - start,
                "method": method,
                "reynolds": reynolds,
                "seed": seed,
            },
            progress_path,
        )
        _write_history(run_dir / "history.csv", history)

    if method == "supervised":
        inputs_np, targets_np = _load_reference_samples(config, reynolds, seed)
        inputs = _tensor(inputs_np, device)
        targets = _tensor(targets_np, device)
        for step in range(start_step + 1, config.pinn.adam_steps + 1) if not adam_complete else ():
            count = min(config.pinn.interior_batch, inputs.shape[0])
            indices = torch.randint(inputs.shape[0], (count,), generator=generator, device=device)
            optimizer.zero_grad(set_to_none=True)
            loss = torch.mean((model(inputs[indices]) - targets[indices]) ** 2)
            loss.backward()
            optimizer.step()
            if step == 1 or step % config.pinn.log_every == 0:
                history.append({"step": step, "total": float(loss.detach().cpu()), "data": float(loss.detach().cpu())})
                _write_history(run_dir / "history.csv", history)
            if not bool(torch.isfinite(loss)):
                raise FloatingPointError(f"Non-finite supervised loss at Adam step {step}")
            if step % config.pinn.checkpoint_every == 0:
                save_progress(step)

        if not adam_complete:
            start_step = config.pinn.adam_steps
            adam_complete = True
            save_progress(start_step, complete=True)

        if config.pinn.lbfgs_steps > 0:
            optimizer_lbfgs = torch.optim.LBFGS(
                model.parameters(), max_iter=config.pinn.lbfgs_steps, line_search_fn="strong_wolfe"
            )
            fixed_inputs = inputs[: min(10_000, inputs.shape[0])]
            fixed_targets = targets[: fixed_inputs.shape[0]]

            def supervised_closure():
                optimizer_lbfgs.zero_grad(set_to_none=True)
                loss = torch.mean((model(fixed_inputs) - fixed_targets) ** 2)
                if not bool(torch.isfinite(loss)):
                    raise FloatingPointError("Non-finite supervised loss during L-BFGS")
                loss.backward()
                return loss

            optimizer_lbfgs.step(supervised_closure)
    else:
        sampled = sample_training_points(config.geometry, config.pinn, seed)
        points = _prepare_points(sampled, device)
        for step in range(start_step + 1, config.pinn.adam_steps + 1) if not adam_complete else ():
            batch = dict(points)
            batch["interior"] = _sample_batch(
                points["interior"], config.pinn.interior_batch, generator
            )
            optimizer.zero_grad(set_to_none=True)
            losses = component_losses(model, batch, reynolds, config)
            should_diagnose = step == 1 or step % config.pinn.balance_every == 0
            norms = {name: math.nan for name in LOSS_NAMES}
            cosine_values = {f"{a}__{b}": math.nan for i, a in enumerate(LOSS_NAMES) for b in LOSS_NAMES[i + 1 :]}
            if should_diagnose:
                norms, cosine_values = gradient_diagnostics(losses, model)
                if method == "balanced":
                    weights = update_adaptive_weights(weights, norms, config)
            total = sum(weights[name] * losses[name] for name in LOSS_NAMES)
            if not bool(torch.isfinite(total)):
                raise FloatingPointError(f"Non-finite PINN loss at Adam step {step}")
            total.backward()
            optimizer.step()
            if step == 1 or step % config.pinn.log_every == 0:
                row: dict[str, float] = {
                    "step": step,
                    "total": float(total.detach().cpu()),
                    "cosine_min": min(cosine_values.values()),
                    "cosine_mean": float(np.mean(list(cosine_values.values()))),
                }
                for pair, value in cosine_values.items():
                    row[f"cosine_{pair}"] = value
                for name in LOSS_NAMES:
                    row[f"loss_{name}"] = float(losses[name].detach().cpu())
                    row[f"weight_{name}"] = weights[name]
                    row[f"grad_{name}"] = norms[name]
                history.append(row)
                _write_history(run_dir / "history.csv", history)
            if step % config.pinn.checkpoint_every == 0:
                save_progress(step)

        if not adam_complete:
            start_step = config.pinn.adam_steps
            adam_complete = True
            save_progress(start_step, complete=True)

        if config.pinn.lbfgs_steps > 0:
            optimizer_lbfgs = torch.optim.LBFGS(
                model.parameters(), max_iter=config.pinn.lbfgs_steps, line_search_fn="strong_wolfe"
            )
            fixed = dict(points)
            fixed["interior"] = points["interior"][: min(10_000, points["interior"].shape[0])]

            def closure():
                optimizer_lbfgs.zero_grad(set_to_none=True)
                losses = component_losses(model, fixed, reynolds, config)
                total = sum(weights[name] * losses[name] for name in LOSS_NAMES)
                if not bool(torch.isfinite(total)):
                    raise FloatingPointError("Non-finite PINN loss during L-BFGS")
                total.backward()
                return total

            optimizer_lbfgs.step(closure)

    training_seconds = elapsed_before_resume + time.perf_counter() - start
    torch.save(
        {
            "state_dict": model.state_dict(),
            "method": method,
            "reynolds": reynolds,
            "seed": seed,
            "weights": weights,
            "config": config.as_dict(),
        },
        checkpoint_path,
    )
    _write_history(run_dir / "history.csv", history)
    (run_dir / "training.json").write_text(
        json.dumps(
            {
                "method": method,
                "reynolds": reynolds,
                "seed": seed,
                "training_seconds": training_seconds,
                "device": str(device),
                "cuda_name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
                "final_weights": weights,
                "config": config.as_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    evaluate_model(config, checkpoint_path)
    if progress_path.exists():
        progress_path.unlink()
    return checkpoint_path


def _batched_predict(model, inputs: np.ndarray, device, batch_size: int) -> tuple[np.ndarray, float]:
    torch = _torch()
    outputs = []
    if device.type == "cuda":
        torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.no_grad():
        for begin in range(0, inputs.shape[0], batch_size):
            batch = _tensor(inputs[begin : begin + batch_size], device)
            outputs.append(model(batch).detach().cpu().numpy())
    if device.type == "cuda":
        torch.cuda.synchronize()
    return np.concatenate(outputs, axis=0), time.perf_counter() - start


def evaluate_model(config: ExperimentConfig, checkpoint_path: Path) -> dict[str, float]:
    torch = _torch()
    device = _device()
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model = CylinderPINNBase.build(config).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    reynolds = int(checkpoint["reynolds"])
    with np.load(config.output_dir / "reference" / f"cylinder_re{reynolds}.npz") as archive:
        reference = {name: archive[name] for name in archive.files}
    xx, yy = np.meshgrid(reference["x"], reference["y"])
    fluid = ~reference["solid"]
    inputs = np.column_stack((xx[fluid], yy[fluid])).astype(np.float32)
    prediction, inference_seconds = _batched_predict(
        model, inputs, device, config.pinn.evaluation_batch
    )
    true_u = reference["u"][fluid]
    true_v = reference["v"][fluid]
    true_p = reference["p"][fluid]
    pred_u, pred_v, pred_p = prediction.T
    pred_p = pred_p - np.mean(pred_p - true_p)
    velocity_error = np.linalg.norm(
        np.column_stack((pred_u - true_u, pred_v - true_v))
    ) / (np.linalg.norm(np.column_stack((true_u, true_v))) + 1.0e-12)
    pressure_error = np.linalg.norm(pred_p - true_p) / (np.linalg.norm(true_p) + 1.0e-12)

    rng = np.random.default_rng(int(checkpoint["seed"]) + 991)
    divergence_count = min(4_096, inputs.shape[0])
    divergence_inputs = inputs[rng.choice(inputs.shape[0], divergence_count, replace=False)]
    xy = _tensor(divergence_inputs, device, requires_grad=True)
    predicted = model(xy)
    grad_u = torch.autograd.grad(predicted[:, 0].sum(), xy, create_graph=False, retain_graph=True)[0]
    grad_v = torch.autograd.grad(predicted[:, 1].sum(), xy, create_graph=False)[0]
    divergence_rms = float(torch.sqrt(torch.mean((grad_u[:, 0] + grad_v[:, 1]) ** 2)).detach().cpu())

    wall_points = sample_training_points(config.geometry, config.pinn, 17).walls
    wall_prediction, _ = _batched_predict(model, wall_points, device, config.pinn.evaluation_batch)
    wall_rms = float(np.sqrt(np.mean(wall_prediction[:, :2] ** 2)))

    theta = np.linspace(0.0, 2.0 * np.pi, 720, endpoint=False, dtype=np.float32)
    circle = np.column_stack(
        (
            config.geometry.cylinder_x + config.geometry.cylinder_radius * np.cos(theta),
            config.geometry.cylinder_y + config.geometry.cylinder_radius * np.sin(theta),
        )
    ).astype(np.float32)
    circle_xy = _tensor(circle, device, requires_grad=True)
    circle_prediction = model(circle_xy)
    circle_u, circle_v, circle_p = circle_prediction[:, 0], circle_prediction[:, 1], circle_prediction[:, 2]
    circle_grad_u = torch.autograd.grad(circle_u.sum(), circle_xy, create_graph=False, retain_graph=True)[0]
    circle_grad_v = torch.autograd.grad(circle_v.sum(), circle_xy, create_graph=False)[0]
    nx = torch.cos(_tensor(theta[:, None], device)).squeeze(1)
    ny = torch.sin(_tensor(theta[:, None], device)).squeeze(1)
    traction_x = (
        -circle_p * nx
        + (2.0 * circle_grad_u[:, 0] * nx + (circle_grad_u[:, 1] + circle_grad_v[:, 0]) * ny)
        / reynolds
    )
    ds = config.geometry.cylinder_radius * (2.0 * np.pi / theta.size)
    # The radial normal points out of the solid into the fluid, so integrating
    # this traction directly gives the streamwise force exerted on the body.
    drag_coefficient = float((2.0 * ds * torch.sum(traction_x)).detach().cpu())

    center_x = np.linspace(
        config.geometry.cylinder_x + config.geometry.cylinder_radius + 1.0e-3,
        min(12.0, config.geometry.length),
        2_000,
        dtype=np.float32,
    )
    centerline = np.column_stack(
        (center_x, np.full_like(center_x, config.geometry.cylinder_y))
    )
    center_prediction, _ = _batched_predict(model, centerline, device, config.pinn.evaluation_batch)
    negative = np.where(center_prediction[:, 0] < 0.0)[0]
    recirculation_length = 0.0 if not negative.size else float(
        center_x[negative[-1]] - (config.geometry.cylinder_x + config.geometry.cylinder_radius)
    )

    shape = reference["solid"].shape
    pred_u_grid = np.full(shape, np.nan)
    pred_v_grid = np.full(shape, np.nan)
    pred_p_grid = np.full(shape, np.nan)
    pred_u_grid[fluid] = pred_u
    pred_v_grid[fluid] = pred_v
    pred_p_grid[fluid] = pred_p
    np.savez_compressed(
        checkpoint_path.parent / "evaluation_fields.npz",
        pred_u=pred_u_grid,
        pred_v=pred_v_grid,
        pred_p=pred_p_grid,
        error_speed=np.sqrt((pred_u_grid - reference["u"]) ** 2 + (pred_v_grid - reference["v"]) ** 2),
    )
    summary = {
        "method": checkpoint["method"],
        "reynolds": reynolds,
        "seed": int(checkpoint["seed"]),
        "velocity_relative_l2": float(velocity_error),
        "pressure_relative_l2": float(pressure_error),
        "divergence_rms": divergence_rms,
        "wall_velocity_rms": wall_rms,
        "drag_coefficient": drag_coefficient,
        "recirculation_length": recirculation_length,
        "inference_seconds": inference_seconds,
        "evaluation_points": int(inputs.shape[0]),
    }
    (checkpoint_path.parent / "evaluation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def train_model(
    config: ExperimentConfig,
    reynolds: int,
    seed: int,
    method: str,
    *,
    force: bool = False,
) -> Path:
    """Train one run and preserve a failure record instead of silently retrying it."""
    run_dir = config.output_dir / "runs" / f"re{reynolds}_{method}_seed{seed}"
    failure_path = run_dir / "failure.json"
    try:
        checkpoint = _train_model_impl(
            config, reynolds, seed, method, force=force
        )
        if failure_path.exists():
            failure_path.unlink()
        return checkpoint
    except Exception as exc:
        run_dir.mkdir(parents=True, exist_ok=True)
        failure_path.write_text(
            json.dumps(
                {
                    "method": method,
                    "reynolds": reynolds,
                    "seed": seed,
                    "failed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "exception_type": type(exc).__name__,
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                    "config": config.as_dict(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raise


def train_experiment(config: ExperimentConfig, *, force: bool = False) -> list[Path]:
    checkpoints: list[Path] = []
    for reynolds in config.reynolds_numbers:
        for method in config.methods:
            for seed in config.seeds:
                checkpoints.append(train_model(config, reynolds, seed, method, force=force))
    return checkpoints

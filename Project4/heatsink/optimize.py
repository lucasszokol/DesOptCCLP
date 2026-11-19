"""Gradient-based fixed-topology and ground-structure optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, NonlinearConstraint, OptimizeResult, minimize

from .model import HeatSinkModel, ResponseResult


@dataclass
class OptimizationHistory:
    designs: list[list[float]] = field(default_factory=list)
    mass_kg: list[float] = field(default_factory=list)
    constraint_margins: list[list[float]] = field(default_factory=list)
    elapsed_seconds: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class OptimizationRun:
    name: str
    result: OptimizeResult
    full_design: np.ndarray
    mass_kg: float
    responses: tuple[ResponseResult, ...]
    history: OptimizationHistory
    method: str
    fixed_topology: bool
    nonlinear: bool
    penalty: float
    initial_design: np.ndarray
    elapsed_seconds: float
    feasibility_tolerance: float
    temperature_reserve_k: float
    temperature_limits_k: tuple[float, ...]

    @property
    def max_scaled_constraint(self) -> float:
        return max(response.scaled_constraint + self.temperature_reserve_k / limit
                   for limit, response in zip(self.temperature_limits_k, self.responses))

    @property
    def feasible(self) -> bool:
        return self.max_scaled_constraint <= self.feasibility_tolerance

    @property
    def accepted(self) -> bool:
        """True only for a successful solver exit with a feasible final design."""

        return bool(self.result.success and self.feasible)


class OptimizationProblem:
    """SciPy interface with cached state and adjoint evaluations."""

    def __init__(
        self,
        model: HeatSinkModel,
        *,
        fixed_topology: bool,
        nonlinear: bool,
        penalty: float,
        frozen_density: np.ndarray | None = None,
    ):
        self.model = model
        self.fixed_topology = fixed_topology
        self.nonlinear = nonlinear
        self.penalty = penalty
        self.count = model.config.geometry.candidate_fins
        if frozen_density is None:
            frozen_density = np.ones(self.count)
        self.frozen_density = np.asarray(frozen_density, dtype=float)
        if self.frozen_density.shape != (self.count,):
            raise ValueError("frozen_density has the wrong shape")
        self.reference_mass = model.mass_kg(model.initial_design())
        self.history = OptimizationHistory()
        self.started_at = perf_counter()
        self._key: bytes | None = None
        self._responses: tuple[ResponseResult, ...] | None = None

    def full_design(self, variables: np.ndarray) -> np.ndarray:
        values = np.asarray(variables, dtype=float)
        if self.fixed_topology:
            if values.shape != (self.count,):
                raise ValueError("fixed-topology variables must be fin heights")
            return np.r_[values, self.frozen_density]
        if values.shape != (2 * self.count,):
            raise ValueError("topology variables must contain heights and densities")
        return values

    def reduced_gradient(self, full_gradient: np.ndarray) -> np.ndarray:
        return full_gradient[: self.count] if self.fixed_topology else full_gradient

    def bounds(self) -> Bounds:
        g = self.model.config.geometry
        hlow, hhigh = g.fin_height_bounds_m
        if self.fixed_topology:
            return Bounds(
                np.full(self.count, hlow),
                np.full(self.count, hhigh),
                keep_feasible=True,
            )
        rlow, rhigh = g.density_bounds
        return Bounds(
            np.r_[np.full(self.count, hlow), np.full(self.count, rlow)],
            np.r_[np.full(self.count, hhigh), np.full(self.count, rhigh)],
            keep_feasible=True,
        )

    def _evaluate(self, variables: np.ndarray) -> tuple[ResponseResult, ...]:
        full = self.full_design(variables)
        key = np.ascontiguousarray(full).tobytes()
        if key != self._key:
            self._responses = tuple(
                self.model.response_with_adjoint(
                    full, case, nonlinear=self.nonlinear, penalty=self.penalty
                )
                for case in self.model.config.load_cases
            )
            self._key = key
        assert self._responses is not None
        return self._responses

    def objective(self, variables: np.ndarray) -> float:
        return self.model.mass_kg(self.full_design(variables)) / self.reference_mass

    def objective_gradient(self, variables: np.ndarray) -> np.ndarray:
        full = self.model.mass_gradient(self.full_design(variables)) / self.reference_mass
        return self.reduced_gradient(full)

    def objective_hessian(self, variables: np.ndarray) -> np.ndarray:
        """Exact mass Hessian, including height/density cross derivatives."""

        size = np.asarray(variables).size
        result = np.zeros((size, size))
        if not self.fixed_topology:
            g, material = self.model.config.geometry, self.model.config.material
            coefficient = material.density_kg_m3 * g.extrusion_depth_m * g.fin_thickness_m / self.reference_mass
            cross = coefficient * self.model.filter_matrix
            result[:self.count, self.count:] = cross
            result[self.count:, :self.count] = cross.T
        return result

    def margins(self, variables: np.ndarray) -> np.ndarray:
        reserve = float(self.model.config.raw["optimization"]["temperature_reserve_k"])
        return -np.array([response.scaled_constraint + reserve / case.chip_limit_k
                          for case, response in zip(self.model.config.load_cases, self._evaluate(variables))])

    def margins_jacobian(self, variables: np.ndarray) -> np.ndarray:
        return np.vstack(
            [-self.reduced_gradient(response.gradient) for response in self._evaluate(variables)]
        )

    def record(self, variables: np.ndarray) -> None:
        full = self.full_design(variables)
        if self.history.designs and np.array_equal(
            np.asarray(self.history.designs[-1]), full
        ):
            return
        self.history.designs.append(full.tolist())
        self.history.mass_kg.append(self.model.mass_kg(full))
        self.history.constraint_margins.append(self.margins(variables).tolist())
        self.history.elapsed_seconds.append(perf_counter() - self.started_at)

    def callback(self, variables: np.ndarray, state: object | None = None) -> None:
        self.record(variables)


def optimize_design(
    model: HeatSinkModel,
    initial_full_design: np.ndarray,
    *,
    name: str,
    fixed_topology: bool,
    nonlinear: bool,
    penalty: float,
    frozen_density: np.ndarray | None = None,
    method: str = "SLSQP",
    max_iterations: int = 250,
) -> OptimizationRun:
    """Run one documented optimization stage with exact gradients."""

    started_at = perf_counter()
    problem = OptimizationProblem(
        model,
        fixed_topology=fixed_topology,
        nonlinear=nonlinear,
        penalty=penalty,
        frozen_density=frozen_density,
    )
    initial = (
        np.asarray(initial_full_design, dtype=float)[: problem.count]
        if fixed_topology
        else np.asarray(initial_full_design, dtype=float)
    )
    initial_full = problem.full_design(initial).copy()
    problem.record(initial)
    if method == "SLSQP":
        constraints = {
            "type": "ineq",
            "fun": problem.margins,
            "jac": problem.margins_jacobian,
        }
        result = minimize(
            problem.objective,
            initial,
            method="SLSQP",
            jac=problem.objective_gradient,
            bounds=problem.bounds(),
            constraints=constraints,
            callback=problem.callback,
            options={"ftol": 1.0e-10, "maxiter": max_iterations, "disp": False},
        )
    elif method == "trust-constr":
        physical_bounds = problem.bounds()
        lower = np.asarray(physical_bounds.lb, dtype=float)
        scale = np.asarray(physical_bounds.ub, dtype=float) - lower
        scaled_initial = (initial - lower) / scale

        def physical(scaled: np.ndarray) -> np.ndarray:
            return lower + scale * np.asarray(scaled, dtype=float)

        def scaled_objective(scaled: np.ndarray) -> float:
            return problem.objective(physical(scaled))

        def scaled_objective_gradient(scaled: np.ndarray) -> np.ndarray:
            return problem.objective_gradient(physical(scaled)) * scale

        def scaled_margins(scaled: np.ndarray) -> np.ndarray:
            return problem.margins(physical(scaled))

        def scaled_margins_jacobian(scaled: np.ndarray) -> np.ndarray:
            return problem.margins_jacobian(physical(scaled)) * scale[None, :]

        def scaled_callback(scaled: np.ndarray, state: object | None = None) -> None:
            problem.callback(physical(scaled), state)

        constraint = NonlinearConstraint(
            scaled_margins, 0.0, np.inf, jac=scaled_margins_jacobian
        )
        result = minimize(
            scaled_objective,
            scaled_initial,
            method="trust-constr",
            jac=scaled_objective_gradient,
            hess=lambda scaled: scale[:, None] * problem.objective_hessian(physical(scaled)) * scale[None, :],
            bounds=Bounds(
                np.zeros_like(scaled_initial),
                np.ones_like(scaled_initial),
                keep_feasible=True,
            ),
            constraints=[constraint],
            callback=scaled_callback,
            options={
                "gtol": 1.0e-10,
                "xtol": 1.0e-12,
                "barrier_tol": 1.0e-12,
                "maxiter": max_iterations,
                "verbose": 0,
            },
        )
        result["scaled_x"] = np.asarray(result.x, dtype=float).copy()
        result.x = physical(result.x)
        result["variable_scale"] = scale
        multipliers = getattr(result, "v", None)
        if multipliers is not None and len(multipliers) >= 2:
            constraint_multipliers = np.asarray(multipliers[0], dtype=float)
            scaled_bound_multipliers = np.asarray(multipliers[1], dtype=float)
            physical_bound_multipliers = scaled_bound_multipliers / scale
            result["constraint_multipliers"] = constraint_multipliers
            result["scaled_bound_multipliers"] = scaled_bound_multipliers
            result["physical_bound_multipliers"] = physical_bound_multipliers
            stationarity = (
                problem.objective_gradient(result.x)
                + problem.margins_jacobian(result.x).T @ constraint_multipliers
                + physical_bound_multipliers
            )
            result["physical_stationarity"] = stationarity
            result["physical_stationarity_inf_norm"] = float(
                np.linalg.norm(stationarity, ord=np.inf)
            )
            margins = problem.margins(result.x)
            result["constraint_complementarity"] = (
                constraint_multipliers * margins
            )
            result["constraint_complementarity_inf_norm"] = float(
                np.linalg.norm(result.constraint_complementarity, ord=np.inf)
            )
            bound_slack = np.where(
                physical_bound_multipliers > 0.0,
                physical_bounds.ub - result.x,
                result.x - physical_bounds.lb,
            )
            result["bound_complementarity"] = (
                physical_bound_multipliers * bound_slack
            )
            result["bound_complementarity_inf_norm"] = float(
                np.linalg.norm(result.bound_complementarity, ord=np.inf)
            )
    else:
        raise ValueError(f"unsupported optimizer {method}")
    full = problem.full_design(result.x)
    responses = problem._evaluate(result.x)
    problem.record(result.x)
    elapsed = perf_counter() - started_at
    feasibility_tolerance = float(
        model.config.raw["optimization"]["scaled_feasibility_tolerance"]
    )
    return OptimizationRun(
        name=name,
        result=result,
        full_design=full,
        mass_kg=model.mass_kg(full),
        responses=responses,
        history=problem.history,
        method=method,
        fixed_topology=fixed_topology,
        nonlinear=nonlinear,
        penalty=float(penalty),
        initial_design=initial_full,
        elapsed_seconds=elapsed,
        feasibility_tolerance=feasibility_tolerance,
        temperature_reserve_k=float(model.config.raw["optimization"]["temperature_reserve_k"]),
        temperature_limits_k=tuple(case.chip_limit_k for case in model.config.load_cases),
    )

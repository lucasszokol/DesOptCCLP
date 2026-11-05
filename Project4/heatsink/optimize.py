"""Gradient-based fixed-topology and ground-structure optimization."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import Bounds, NonlinearConstraint, OptimizeResult, minimize

from .model import HeatSinkModel, ResponseResult


@dataclass
class OptimizationHistory:
    designs: list[list[float]] = field(default_factory=list)
    mass_kg: list[float] = field(default_factory=list)
    constraint_margins: list[list[float]] = field(default_factory=list)


@dataclass(frozen=True)
class OptimizationRun:
    name: str
    result: OptimizeResult
    full_design: np.ndarray
    mass_kg: float
    responses: tuple[ResponseResult, ...]
    history: OptimizationHistory


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
            return Bounds(np.full(self.count, hlow), np.full(self.count, hhigh))
        rlow, rhigh = g.density_bounds
        return Bounds(
            np.r_[np.full(self.count, hlow), np.full(self.count, rlow)],
            np.r_[np.full(self.count, hhigh), np.full(self.count, rhigh)],
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

    def margins(self, variables: np.ndarray) -> np.ndarray:
        return -np.array([response.scaled_constraint for response in self._evaluate(variables)])

    def margins_jacobian(self, variables: np.ndarray) -> np.ndarray:
        return np.vstack(
            [-self.reduced_gradient(response.gradient) for response in self._evaluate(variables)]
        )

    def callback(self, variables: np.ndarray, state: object | None = None) -> None:
        full = self.full_design(variables)
        self.history.designs.append(full.tolist())
        self.history.mass_kg.append(self.model.mass_kg(full))
        self.history.constraint_margins.append(self.margins(variables).tolist())


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
        constraint = NonlinearConstraint(
            problem.margins, 0.0, np.inf, jac=problem.margins_jacobian
        )
        result = minimize(
            problem.objective,
            initial,
            method="trust-constr",
            jac=problem.objective_gradient,
            bounds=problem.bounds(),
            constraints=[constraint],
            callback=problem.callback,
            options={"gtol": 1.0e-8, "maxiter": max_iterations, "verbose": 0},
        )
    else:
        raise ValueError(f"unsupported optimizer {method}")
    full = problem.full_design(result.x)
    responses = problem._evaluate(result.x)
    return OptimizationRun(
        name=name,
        result=result,
        full_design=full,
        mass_kg=model.mass_kg(full),
        responses=responses,
        history=problem.history,
    )

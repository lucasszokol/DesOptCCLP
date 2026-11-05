"""Coupled 2D-base/1D-fin thermal finite-element model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import LoadCase, ProjectConfig
from .elements import line_conduction_matrix, quad4_conduction_matrix
from .topology import density_filter, filtered_density, simp_factor


@dataclass(frozen=True)
class SolveResult:
    temperature_k: np.ndarray
    residual_history: tuple[float, ...]
    iterations: int
    converged: bool
    input_power_w: float
    surface_loss_w: float
    energy_imbalance_w: float


@dataclass(frozen=True)
class ResponseResult:
    """A solved load case and its discrete-adjoint temperature constraint."""

    solve: SolveResult
    ks_temperature_k: float
    scaled_constraint: float
    gradient: np.ndarray


class HeatSinkModel:
    """Dense reference implementation sized for verification and optimization."""

    def __init__(self, config: ProjectConfig):
        self.config = config
        g = config.geometry
        self.nx, self.nz = g.base_elements_x, g.base_elements_z
        self.x = np.linspace(-0.5 * g.base_width_m, 0.5 * g.base_width_m, self.nx + 1)
        self.z = np.linspace(0.0, g.base_thickness_m, self.nz + 1)
        self.base_coordinates = np.array([(x, z) for z in self.z for x in self.x])
        self.base_dofs = len(self.base_coordinates)
        self.quads = self._make_quads()
        step = self.nx // g.candidate_fins
        self.fin_x_indices = np.arange(step // 2, self.nx, step, dtype=int)
        if len(self.fin_x_indices) != g.candidate_fins:
            raise ValueError("mesh cannot place every candidate fin")
        top_offset = self.nz * (self.nx + 1)
        self.fin_roots = top_offset + self.fin_x_indices
        self.fin_dofs = []
        cursor = self.base_dofs
        for root in self.fin_roots:
            dofs = np.r_[root, np.arange(cursor, cursor + g.fin_elements)]
            self.fin_dofs.append(dofs)
            cursor += g.fin_elements
        self.fin_dofs = tuple(self.fin_dofs)
        self.ndof = cursor
        self.filter_matrix = density_filter(
            g.candidate_fins, float(config.raw["optimization"]["filter_radius_fins"])
        )
        self.base_matrix = self._assemble_base_matrix()

    def _node(self, ix: int, iz: int) -> int:
        return iz * (self.nx + 1) + ix

    def _make_quads(self) -> tuple[np.ndarray, ...]:
        quads = []
        for iz in range(self.nz):
            for ix in range(self.nx):
                quads.append(
                    np.array(
                        [
                            self._node(ix, iz),
                            self._node(ix + 1, iz),
                            self._node(ix + 1, iz + 1),
                            self._node(ix, iz + 1),
                        ]
                    )
                )
        return tuple(quads)

    def _assemble_base_matrix(self) -> np.ndarray:
        matrix = np.zeros((self.ndof, self.ndof))
        material = self.config.material
        depth = self.config.geometry.extrusion_depth_m
        for dofs in self.quads:
            local = quad4_conduction_matrix(
                self.base_coordinates[dofs], material.conductivity_w_mk, depth
            )
            matrix[np.ix_(dofs, dofs)] += local
        return matrix

    def initial_design(self, height_m: float = 0.030) -> np.ndarray:
        count = self.config.geometry.candidate_fins
        low, high = self.config.geometry.fin_height_bounds_m
        if not low <= height_m <= high:
            raise ValueError("initial height outside configured bounds")
        return np.r_[np.full(count, height_m), np.ones(count)]

    def split_design(self, design: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        count = self.config.geometry.candidate_fins
        design = np.asarray(design, dtype=float)
        if design.shape != (2 * count,):
            raise ValueError(f"design must have shape ({2 * count},)")
        heights = design[:count]
        raw_density = design[count:]
        filtered = filtered_density(raw_density, self.filter_matrix)
        return heights, raw_density, filtered

    def mass_kg(self, design: np.ndarray) -> float:
        heights, _, density = self.split_design(design)
        g, m = self.config.geometry, self.config.material
        base = g.base_width_m * g.base_thickness_m * g.extrusion_depth_m
        fins = g.extrusion_depth_m * g.fin_thickness_m * np.dot(density, heights)
        return float(m.density_kg_m3 * (base + fins))

    def mass_gradient(self, design: np.ndarray) -> np.ndarray:
        """Exact derivative of mass with respect to heights and raw densities."""

        heights, _, density = self.split_design(design)
        g, m = self.config.geometry, self.config.material
        coefficient = m.density_kg_m3 * g.extrusion_depth_m * g.fin_thickness_m
        height_gradient = coefficient * density
        raw_density_gradient = self.filter_matrix.T @ (coefficient * heights)
        return np.r_[height_gradient, raw_density_gradient]

    def chip_dofs(self) -> np.ndarray:
        half = 0.5 * self.config.geometry.chip_width_m + 1.0e-14
        return np.flatnonzero(np.abs(self.x) <= half)

    def _surface_flux(self, temperature: float, ambient: float, nonlinear: bool) -> tuple[float, float]:
        p = self.config.raw["physics"]
        delta = temperature - ambient
        if nonlinear:
            smooth = np.sqrt(delta * delta + float(p["ambient_smoothing_delta_k"]) ** 2)
            href = float(p["nonlinear_h_reference_w_m2k"])
            dref = float(p["nonlinear_h_reference_delta_k"])
            h = href * (smooth / dref) ** 0.25
            dh = h * 0.25 * delta / (smooth * smooth)
            convection = h * delta
            dconvection = h + delta * dh
            sigma = float(p["stefan_boltzmann_w_m2k4"])
            epsilon = self.config.material.emissivity
            radiation = epsilon * sigma * (temperature**4 - ambient**4)
            dradiation = 4.0 * epsilon * sigma * temperature**3
            return convection + radiation, dconvection + dradiation
        h = float(p["linear_h_w_m2k"])
        return h * delta, h

    def assemble(
        self,
        temperature: np.ndarray,
        design: np.ndarray,
        case: LoadCase,
        *,
        nonlinear: bool,
        penalty: float,
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """Return residual, consistent tangent, and integrated surface loss."""

        t = np.asarray(temperature, dtype=float)
        if t.shape != (self.ndof,):
            raise ValueError(f"temperature must have shape ({self.ndof},)")
        heights, _, density = self.split_design(design)
        g, material = self.config.geometry, self.config.material
        floor = float(self.config.raw["optimization"]["simp_density_floor"])
        conduction_scale = simp_factor(density, penalty, floor)
        residual = self.base_matrix @ t
        tangent = self.base_matrix.copy()
        surface_loss = 0.0

        gauss = (-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))
        for i, dofs in enumerate(self.fin_dofs):
            length = heights[i] / g.fin_elements
            area = g.fin_thickness_m * g.extrusion_depth_m * conduction_scale[i]
            perimeter = 2.0 * (g.extrusion_depth_m + g.fin_thickness_m) * density[i]
            conduction = line_conduction_matrix(material.conductivity_w_mk, area, length)
            for pair in zip(dofs[:-1], dofs[1:]):
                element = np.asarray(pair, dtype=int)
                residual[element] += conduction @ t[element]
                tangent[np.ix_(element, element)] += conduction
                for xi in gauss:
                    shape = 0.5 * np.array([1.0 - xi, 1.0 + xi])
                    value = float(shape @ t[element])
                    flux, derivative = self._surface_flux(value, case.ambient_k, nonlinear)
                    weight = perimeter * 0.5 * length
                    residual[element] += weight * shape * flux
                    tangent[np.ix_(element, element)] += weight * derivative * np.outer(shape, shape)
                    surface_loss += weight * flux

            tip = int(dofs[-1])
            tip_area = g.fin_thickness_m * g.extrusion_depth_m * density[i]
            flux, derivative = self._surface_flux(float(t[tip]), case.ambient_k, nonlinear)
            residual[tip] += tip_area * flux
            tangent[tip, tip] += tip_area * derivative
            surface_loss += tip_area * flux

        # Exposed horizontal base top, integrated with two-node edge elements.
        top = self.nz * (self.nx + 1)
        edge_length = g.base_width_m / self.nx
        for ix in range(self.nx):
            edge = np.array([top + ix, top + ix + 1])
            for xi in gauss:
                shape = 0.5 * np.array([1.0 - xi, 1.0 + xi])
                value = float(shape @ t[edge])
                flux, derivative = self._surface_flux(value, case.ambient_k, nonlinear)
                weight = g.extrusion_depth_m * 0.5 * edge_length
                residual[edge] += weight * shape * flux
                tangent[np.ix_(edge, edge)] += weight * derivative * np.outer(shape, shape)
                surface_loss += weight * flux

        # Uniform chip heat flux on selected bottom edges; distribute exactly.
        half = 0.5 * g.chip_width_m
        selected = [ix for ix in range(self.nx) if abs(0.5 * (self.x[ix] + self.x[ix + 1])) <= half]
        if not selected:
            raise RuntimeError("chip region has no boundary edges")
        edge_power = case.power_w / len(selected)
        for ix in selected:
            edge = np.array([ix, ix + 1])
            residual[edge] -= 0.5 * edge_power
        return residual, tangent, float(surface_loss)

    def assemble_design_jacobian(
        self,
        temperature: np.ndarray,
        design: np.ndarray,
        case: LoadCase,
        *,
        nonlinear: bool,
        penalty: float,
    ) -> np.ndarray:
        """Analytic partial derivative ``dR/dx`` at fixed temperature."""

        t = np.asarray(temperature, dtype=float)
        heights, _, density = self.split_design(design)
        g, material = self.config.geometry, self.config.material
        count = g.candidate_fins
        floor = float(self.config.raw["optimization"]["simp_density_floor"])
        conduction_scale = simp_factor(density, penalty, floor)
        conduction_scale_derivative = (
            (1.0 - floor) * penalty * density ** (penalty - 1.0)
        )
        by_height = np.zeros((self.ndof, count))
        by_filtered_density = np.zeros((self.ndof, count))
        gauss = (-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))

        for i, dofs in enumerate(self.fin_dofs):
            length = heights[i] / g.fin_elements
            area = g.fin_thickness_m * g.extrusion_depth_m * conduction_scale[i]
            perimeter_coefficient = 2.0 * (g.extrusion_depth_m + g.fin_thickness_m)
            perimeter = perimeter_coefficient * density[i]
            conduction = line_conduction_matrix(material.conductivity_w_mk, area, length)
            conduction_height_derivative = -conduction / heights[i]
            conduction_density_derivative = (
                conduction * conduction_scale_derivative[i] / conduction_scale[i]
            )

            for pair in zip(dofs[:-1], dofs[1:]):
                element = np.asarray(pair, dtype=int)
                local_temperature = t[element]
                by_height[element, i] += conduction_height_derivative @ local_temperature
                by_filtered_density[element, i] += conduction_density_derivative @ local_temperature
                for xi in gauss:
                    shape = 0.5 * np.array([1.0 - xi, 1.0 + xi])
                    value = float(shape @ local_temperature)
                    flux, _ = self._surface_flux(value, case.ambient_k, nonlinear)
                    weight = perimeter * 0.5 * length
                    # L = H / n, so d(weight)/dH = weight/H.
                    by_height[element, i] += (weight / heights[i]) * shape * flux
                    # P = coefficient * rho, so d(weight)/drho excludes rho.
                    density_weight = perimeter_coefficient * 0.5 * length
                    by_filtered_density[element, i] += density_weight * shape * flux

            tip = int(dofs[-1])
            flux, _ = self._surface_flux(float(t[tip]), case.ambient_k, nonlinear)
            by_filtered_density[tip, i] += (
                g.fin_thickness_m * g.extrusion_depth_m * flux
            )

        by_raw_density = by_filtered_density @ self.filter_matrix
        return np.hstack((by_height, by_raw_density))

    def ks_temperature(self, temperature: np.ndarray) -> tuple[float, np.ndarray]:
        """Smooth maximum of chip-interface temperature and its state gradient."""

        chip = self.chip_dofs()
        values = np.asarray(temperature, dtype=float)[chip]
        rho = float(self.config.raw["physics"]["ks_rho_per_k"])
        maximum = float(values.max())
        exponent = np.exp(rho * (values - maximum))
        weights = exponent / exponent.sum()
        value = maximum + np.log(exponent.sum()) / rho
        gradient = np.zeros(self.ndof)
        gradient[chip] = weights
        return float(value), gradient

    def response_with_adjoint(
        self,
        design: np.ndarray,
        case: LoadCase,
        *,
        nonlinear: bool = True,
        penalty: float = 3.0,
    ) -> ResponseResult:
        """Solve a load case and return the exact discrete-adjoint gradient."""

        solved = self.solve(design, case, nonlinear=nonlinear, penalty=penalty)
        if not solved.converged:
            raise RuntimeError(f"load case {case.name} did not converge")
        ks, dks_dt = self.ks_temperature(solved.temperature_k)
        _, tangent, _ = self.assemble(
            solved.temperature_k, design, case, nonlinear=nonlinear, penalty=penalty
        )
        residual_design = self.assemble_design_jacobian(
            solved.temperature_k, design, case, nonlinear=nonlinear, penalty=penalty
        )
        # g = KS / limit - 1.  The residual has no explicit dependence on g.
        dg_dt = dks_dt / case.chip_limit_k
        adjoint = np.linalg.solve(tangent.T, -dg_dt)
        gradient = adjoint @ residual_design
        return ResponseResult(
            solve=solved,
            ks_temperature_k=ks,
            scaled_constraint=ks / case.chip_limit_k - 1.0,
            gradient=np.asarray(gradient),
        )

    def solve(
        self,
        design: np.ndarray,
        case: LoadCase,
        *,
        nonlinear: bool = True,
        penalty: float = 3.0,
        initial_temperature: np.ndarray | None = None,
    ) -> SolveResult:
        settings = self.config.raw["solver"]
        if initial_temperature is None:
            temperature = np.full(self.ndof, case.ambient_k + 20.0)
        else:
            temperature = np.asarray(initial_temperature, dtype=float).copy()
        history: list[float] = []
        initial_norm = None
        surface_loss = np.nan
        for iteration in range(int(settings["newton_max_iterations"])):
            residual, tangent, surface_loss = self.assemble(
                temperature, design, case, nonlinear=nonlinear, penalty=penalty
            )
            norm = float(np.linalg.norm(residual))
            history.append(norm)
            if initial_norm is None:
                initial_norm = max(norm, 1.0)
            if norm <= float(settings["newton_absolute_tolerance"]) + float(settings["newton_relative_tolerance"]) * initial_norm:
                return SolveResult(temperature, tuple(history), iteration, True, case.power_w, surface_loss, surface_loss - case.power_w)
            step = np.linalg.solve(tangent, -residual)
            alpha = 1.0
            minimum = float(settings["line_search_minimum"])
            while alpha >= minimum:
                trial = temperature + alpha * step
                trial_residual, _, _ = self.assemble(trial, design, case, nonlinear=nonlinear, penalty=penalty)
                if np.linalg.norm(trial_residual) < (1.0 - 1.0e-4 * alpha) * norm:
                    temperature = trial
                    break
                alpha *= 0.5
            else:
                raise RuntimeError("Newton line search failed")
        return SolveResult(temperature, tuple(history), int(settings["newton_max_iterations"]), False, case.power_w, surface_loss, surface_loss - case.power_w)

"""Cross-check the production fin assembly against an independent BVP solver.

This is supplementary numerical evidence, not a student-derived exact solution.
"""
from dataclasses import replace

import numpy as np
from scipy.integrate import solve_bvp

from .config import LoadCase
from .model import HeatSinkModel


def nonlinear_fin_check(model: HeatSinkModel) -> dict:
    g, material, p = model.config.geometry, model.config.material, model.config.raw["physics"]
    length, root, ambient = 0.050, 353.15, 298.15
    area = g.fin_thickness_m * g.extrusion_depth_m
    perimeter = 2.0 * (g.extrusion_depth_m + g.fin_thickness_m)
    conductivity = material.conductivity_w_mk

    # Independently formulate the continuum BVP: k A T'' = P q(T),
    # T(0)=root and -k A T'(L)=A q(T(L)).
    def flux(t):
        d = t - ambient
        h = p["nonlinear_h_reference_w_m2k"] * ((d*d + p["ambient_smoothing_delta_k"]**2)**0.5 / p["nonlinear_h_reference_delta_k"])**0.25
        return h*d + material.emissivity*p["stefan_boltzmann_w_m2k4"]*(t**4 - ambient**4)

    def ode(_x, y):
        return np.vstack((y[1], perimeter * flux(y[0]) / (conductivity * area)))

    def bc(left, right):
        return np.array([left[0]-root, -conductivity*right[1]-flux(right[0])])

    x = np.linspace(0.0, length, 25)
    guess = np.vstack((np.full_like(x, root), np.zeros_like(x)))
    reference = solve_bvp(ode, bc, x, guess, tol=1e-9, max_nodes=5000)
    if not reference.success:
        raise RuntimeError(f"Independent fin BVP failed: {reference.message}")

    records = []
    for n in (8, 16):
        local = HeatSinkModel(replace(model.config, geometry=replace(g, fin_elements=n)))
        design = local.initial_design(length)
        case = LoadCase("fin_verification", 0.0, ambient, root)
        dofs = local.fin_dofs[0][1:]
        state = np.full(local.ndof, root)
        norms = []
        for _ in range(12):
            residual, tangent, _ = local.assemble(state, design, case, nonlinear=True, penalty=1.0)
            norm = float(np.linalg.norm(residual[dofs]))
            norms.append(norm)
            if norm < 1e-11:
                break
            state[dofs] += np.linalg.solve(tangent[np.ix_(dofs, dofs)], -residual[dofs])
        if norms[-1] >= 1e-11:
            raise RuntimeError("Production fin assembly did not converge")
        nodes = np.linspace(0.0, length, n+1)
        reference_values = reference.sol(nodes)[0]
        computed = state[local.fin_dofs[0]]
        error = float(np.max(np.abs(computed-reference_values)))
        direction = np.linspace(-0.7, 1.0, n)
        perturbation = np.zeros(local.ndof)
        perturbation[dofs] = direction
        step = 1e-4
        plus = local.assemble(state + step*perturbation, design, case, nonlinear=True, penalty=1.0)[0][dofs]
        minus = local.assemble(state - step*perturbation, design, case, nonlinear=True, penalty=1.0)[0][dofs]
        analytic = tangent[np.ix_(dofs, dofs)] @ direction
        tangent_error = float(np.linalg.norm((plus-minus)/(2*step)-analytic) / np.linalg.norm(analytic))
        records.append({"elements": n, "maximum_nodal_error_k": error,
                        "tip_fe_k": float(computed[-1]), "tip_bvp_k": float(reference_values[-1]),
                        "residual_norms": norms,
                        "quadratic_residual_ratios": [norms[i+1]/norms[i]**2 for i in range(min(2, len(norms)-1))],
                        "tangent_direction_relative_error": tangent_error})
    # Fixed engineering tolerance and a mesh-refinement check, not a claim of
    # an exact analytical solution or externally validated heat-transfer model.
    passed = (records[0]["maximum_nodal_error_k"] < 0.1
              and records[1]["maximum_nodal_error_k"] < records[0]["maximum_nodal_error_k"]
              and all(row["tangent_direction_relative_error"] < 1e-6
                      and len(row["quadratic_residual_ratios"]) == 2
                      and max(row["quadratic_residual_ratios"]) < 1 for row in records))
    return {"status": "passed" if passed else "failed", "description": "Production fin residual and tangent with prescribed root temperature compared with scipy.integrate.solve_bvp; the reference is numerical, not student-derived exact truth.",
            "length_m": length, "root_k": root, "ambient_k": ambient,
            "reference_solver_tolerance": 1e-9, "coarse_error_tolerance_k": 0.1, "meshes": records}

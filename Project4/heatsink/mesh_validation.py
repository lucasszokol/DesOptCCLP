"""Reanalyse final designs on refined meshes without re-optimizing them."""
from dataclasses import replace

from .model import HeatSinkModel


def validate_design_meshes(model, nominal_design, robust_model, robust_design):
    g = model.config.geometry
    tolerance_k = float(model.config.raw["verification"]["mesh_temperature_change_tolerance_k"])
    scaled_tolerance = float(model.config.raw["optimization"]["scaled_feasibility_tolerance"])
    # Keep all fin roots at identical physical positions on every mesh.
    meshes = ((g.base_elements_x, g.base_elements_z), (160, 16), (320, 32), (400, 40))
    if meshes[0] != (40, 4):
        raise ValueError("Mesh verification requires the documented 40-by-4 reference mesh")
    rows = []
    for nx, nz in meshes:
        refined = HeatSinkModel(replace(model.config, geometry=replace(g, base_elements_x=nx, base_elements_z=nz)))
        checks = [("nominal design", nominal_design, case) for case in model.config.load_cases]
        checks += [("uncertainty design", robust_design, case) for case in robust_model.config.load_cases]
        for design_name, design, case in checks:
            state = refined.solve(design, case, nonlinear=True, penalty=3.0)
            if not state.converged:
                raise RuntimeError(f"Mesh reanalysis did not converge: {design_name}/{case.name}")
            ks, _ = refined.ks_temperature(state.temperature_k)
            peak = refined.chip_peak_temperature(state.temperature_k)
            rows.append({"design": design_name, "case": case.name, "base_elements_x": nx,
                         "base_elements_z": nz, "ks_temperature_k": float(ks),
                         "chip_peak_temperature_k": peak, "limit_k": case.chip_limit_k,
                         "passed": bool(ks <= case.chip_limit_k * (1 + scaled_tolerance)
                                        and peak <= case.chip_limit_k)})
    changes = []
    for design_name, _, case in checks:
        study = [r for r in rows if r["design"] == design_name and r["case"] == case.name]
        change = abs(study[-1]["ks_temperature_k"] - study[-2]["ks_temperature_k"])
        changes.append({"design": design_name, "case": case.name, "last_refinement_change_k": change,
                        "passed": bool(change <= tolerance_k)})
    passed = all(row["passed"] for row in rows) and all(row["passed"] for row in changes)
    return {"status": "passed" if passed else "failed", "tolerance_k": tolerance_k,
            "description": "Fixed physical KS sample points; original and refined base meshes; design held fixed. The last two meshes are compared, not a proof of an infinite-mesh or real-world limit.",
            "cases": rows, "last_refinement_changes": changes}

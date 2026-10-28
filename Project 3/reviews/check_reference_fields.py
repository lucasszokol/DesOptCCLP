"""Read-only diagnostics of saved LBM fields; run from Project 3."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

def diagnose(path: Path) -> dict:
    with np.load(path) as z:
        x, y, u, v, p, solid = (z[k] for k in ("x", "y", "u", "v", "p", "solid"))
    dx, dy = float(x[1]-x[0]), float(y[1]-y[0])
    fluid = ~solid
    q = np.nansum(u, axis=0) * dy
    # Central differences only where the complete five-point stencil is fluid.
    du = (u[1:-1,2:] - u[1:-1,:-2]) / (2*dx)
    dv = (v[2:,1:-1] - v[:-2,1:-1]) / (2*dy)
    valid = (fluid[1:-1,1:-1] & fluid[1:-1,2:] & fluid[1:-1,:-2]
             & fluid[2:,1:-1] & fluid[:-2,1:-1])
    div = du + dv
    xx, yy = np.meshgrid(x[1:-1], y[1:-1])
    r = np.hypot(xx-2.0, yy-2.0)
    regions = {"all_valid": valid, "away_from_solids": valid & (r>0.75) & (yy>0.25) & (yy<3.85),
               "wake": valid & (xx>2.75) & (xx<8.0) & (yy>1.0) & (yy<3.0),
               "last_2D": valid & (xx>20.0)}
    stats = {}
    for name, mask in regions.items():
        a = div[mask]
        stats[name] = {"points": int(a.size), "rms": float(np.sqrt(np.mean(a*a))),
                       "max_abs": float(np.max(np.abs(a)))}
    row = int(np.argmin(abs(y-2.0)))
    ids = np.flatnonzero((x>2.5) & np.isfinite(u[row]) & (u[row]<0))
    reattachment = None
    if ids.size and ids[-1]+1 < len(x):
        a = int(ids[-1]); b = a+1
        reattachment = float(x[a]-u[row,a]*(x[b]-x[a])/(u[row,b]-u[row,a])-2.5)
    target = 6*y*(4.1-y)/4.1**2
    ol = slice(1,-1)
    scale = float(np.sum(u[ol,0]) / np.sum(u[ol,-2]))
    pressure_span = float(np.nanmax(p)-np.nanmin(p))
    # rho = rho_out_mean + 3*U_lattice**2*p; equal Q cancels the unknown gauge density.
    mass_flux_difference = float(3*0.05**3*(np.sum(p[ol,0]*u[ol,0])-np.sum(p[ol,-1]*u[ol,-1])))
    mass_difference_per_unit_outlet_density = mass_flux_difference / float(0.05*np.sum(u[ol,0]))
    return {
        "path": str(path), "shape": list(u.shape), "dx": dx, "dy": dy,
        "dy_over_dx": dy/dx,
        "finite_fluid": bool(all(np.all(np.isfinite(a[fluid])) for a in (u,v,p))),
        "inlet_max_abs_error": float(np.max(abs(u[ol,0]-target[ol]))),
        "inlet_max_abs_v": float(np.max(abs(v[ol,0]))),
        "volume_flux_in": float(q[0]), "volume_flux_out": float(q[-1]),
        "max_section_volume_flux_relative_departure": float(np.max(abs(q-q[0]))/abs(q[0])),
        "penultimate_scale_from_final_field": scale,
        "outlet_du_dx_rms": float(np.sqrt(np.mean(((u[ol,-1]-u[ol,-2])/dx)**2))),
        "outlet_dv_dx_rms": float(np.sqrt(np.mean(((v[ol,-1]-v[ol,-2])/dx)**2))),
        "outlet_pressure_mean": float(np.mean(p[ol,-1])),
        "outlet_pressure_rms": float(np.sqrt(np.mean(p[ol,-1]**2))),
        "outlet_pressure_max_abs": float(np.max(abs(p[ol,-1]))),
        "pressure_span": pressure_span,
        "in_minus_out_density_weighted_flux_lattice": mass_flux_difference,
        "mass_flux_difference_over_inlet_volume_flux": mass_difference_per_unit_outlet_density,
        "density_span_lattice": 3*0.05**2*pressure_span,
        "max_speed": float(np.nanmax(np.hypot(u,v))),
        "mach_max": float(np.nanmax(np.hypot(u,v)))*0.05*np.sqrt(3),
        "recirculation_length_interpolated_at_nearest_row": reattachment,
        "center_row_y": float(y[row]), "wake_min_center_u": float(np.nanmin(u[row,x>2.5])),
        "divergence": stats,
    }

def compare(fine_path: Path, coarse_path: Path) -> dict:
    # NumPy implementation of bilinear interpolation, retaining NaN stencil exclusion.
    with np.load(fine_path) as f, np.load(coarse_path) as c:
        xx, yy = np.meshgrid(c["x"],c["y"])
        ix = np.clip(np.searchsorted(f["x"],xx,side="right")-1,0,len(f["x"])-2)
        iy = np.clip(np.searchsorted(f["y"],yy,side="right")-1,0,len(f["y"])-2)
        tx=(xx-f["x"][ix])/(f["x"][ix+1]-f["x"][ix])
        ty=(yy-f["y"][iy])/(f["y"][iy+1]-f["y"][iy])
        def interp(a):
            return ((1-tx)*(1-ty)*a[iy,ix]+tx*(1-ty)*a[iy,ix+1]
                    +(1-tx)*ty*a[iy+1,ix]+tx*ty*a[iy+1,ix+1])
        fu,fv=interp(f["u"]),interp(f["v"])
        valid=(~c["solid"]) & np.isfinite(fu) & np.isfinite(fv)
        masks={"all":valid, "wake":valid & (xx>2.5) & (xx<8) & (yy>1) & (yy<3),
               "last_2D":valid & (xx>20)}
        result={}
        for name, mask in masks.items():
            e=np.column_stack((c["u"][mask]-fu[mask],c["v"][mask]-fv[mask]))
            a=np.column_stack((fu[mask],fv[mask]))
            result[name]={"points":int(mask.sum()),"relative_l2":float(np.linalg.norm(e)/np.linalg.norm(a))}
        result["coarse_fluid_points"]=int((~c["solid"]).sum())
        result["excluded_coarse_fluid_points"]=int((~c["solid"]).sum()-valid.sum())
        return result

if __name__ == "__main__":
    root=Path("project3_results")
    fine=root/"reference/cylinder_re10.npz"
    coarse=root/"grid_check/coarse/reference/cylinder_re10.npz"
    print(json.dumps({"fine":diagnose(fine),"coarse":diagnose(coarse),
                      "comparison":compare(fine,coarse)},indent=2))

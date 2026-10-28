"""Independent implementation checks; no production-source edits or long CFD runs."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
from project3_pinn.config import ExperimentConfig, LBMConfig
from project3_pinn import lbm
from reviews.check_reference_fields import diagnose

class ReferenceImplementationTests(unittest.TestCase):
    def test_variable_density_equilibrium_recovers_first_and_second_moments(self):
        rng = np.random.default_rng(314)
        rho = rng.uniform(0.9, 1.1, (5, 7))
        ux, uy = rng.uniform(-0.08, 0.08, (2, 5, 7))
        f = lbm.equilibrium(rho, ux, uy)
        r, u, v = lbm._macroscopic(f, np.ones(rho.shape, dtype=bool))
        for actual, expected in ((r,rho),(u,ux),(v,uy)):
            np.testing.assert_allclose(actual, expected, atol=2e-15, rtol=0)
        for a in range(2):
            for b in range(2):
                moment = np.sum(f*lbm.C[:,a,None,None]*lbm.C[:,b,None,None],axis=0)
                vel = (ux,uy)
                expected = rho*(vel[a]*vel[b]+(1/3 if a==b else 0))
                np.testing.assert_allclose(moment, expected, atol=2e-15, rtol=0)

    def test_actual_collision_streaming_and_bounceback_on_one_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = replace(ExperimentConfig(), output_dir=Path(tmp), lbm=LBMConfig(
                nodes_per_diameter=8, lattice_mean_velocity=0.05,
                max_steps=1,min_steps=1,check_every=1,convergence_tolerance=0))
            observed = []
            original = lbm._macroscopic
            def observe(f, fluid):
                # Copies distinguish pre-collision f from the mutated final arrays.
                observed.append((f.copy(),fluid.copy()))
                return original(f,fluid)
            with patch.object(lbm,"_macroscopic",side_effect=observe):
                lbm.run_lbm(cfg,10)
            initial, fluid = observed[0]
            final = observed[-1][0]
            # Initial state is an equilibrium; collision leaves it unchanged.
            # At an unobstructed interior destination, populations move along C.
            for i,(cx,cy) in enumerate(lbm.C):
                y,x = 16,80
                self.assertAlmostEqual(final[i,y,x], initial[i,y-int(cy),x-int(cx)],places=14)
            # Every blocked link returns its outgoing population to the same fluid node.
            # Exclude x boundaries, whose reconstruction deliberately takes precedence.
            for i,(cx,cy) in enumerate(lbm.C[1:],start=1):
                neighbor = np.roll(np.roll(~fluid,-int(cy),axis=0),-int(cx),axis=1) & fluid
                neighbor[:,[0,-1]]=False
                np.testing.assert_allclose(final[lbm.OPPOSITE[i],neighbor],
                                           initial[i,neighbor],atol=2e-15,rtol=0)
            r,u,v = original(final,fluid)
            yy=np.arange(u.shape[0]); h=u.shape[0]-1
            target=6*0.05*yy*(h-yy)/h**2
            np.testing.assert_allclose(u[1:-1,0],target[1:-1],atol=2e-15,rtol=0)
            np.testing.assert_allclose(v[1:-1,0],0,atol=2e-15,rtol=0)
            self.assertAlmostEqual(float(u[1:-1,-1].sum()),float(u[1:-1,0].sum()),places=13)

    def test_actual_bgk_collision_conserves_mass_and_momentum_out_of_equilibrium(self):
        # Observe the populations supplied by the real run_lbm to its streaming step.
        with tempfile.TemporaryDirectory() as tmp:
            cfg=replace(ExperimentConfig(),output_dir=Path(tmp),lbm=LBMConfig(
                nodes_per_diameter=6,max_steps=2,min_steps=2,check_every=2,
                convergence_tolerance=0))
            original_eq=lbm.equilibrium
            original_roll=lbm.np.roll
            collision_inputs=[]
            post_populations=[]
            def eq(rho,u,v):
                f=original_eq(rho,u,v)
                if not collision_inputs:
                    # Seed a small non-equilibrium stress with zero mass/momentum.
                    f[1,10,60]+=0.001
                    f[3,10,60]+=0.001
                    f[0,10,60]-=0.002
                collision_inputs.append(f.copy())
                return f
            def roll(a,shift,axis=None):
                # The first (y) roll for each population receives post[i].
                if a.ndim==2 and axis==0 and len(post_populations)<9:
                    post_populations.append(a.copy())
                return original_roll(a,shift,axis=axis)
            with patch.object(lbm,"equilibrium",side_effect=eq), patch.object(lbm.np,"roll",side_effect=roll):
                lbm.run_lbm(cfg,10)
            initial=collision_inputs[0]
            post=np.stack(post_populations)
            self.assertGreater(float(np.max(abs(initial-post))),1e-4)
            np.testing.assert_allclose(post.sum(axis=0),initial.sum(axis=0),atol=2e-15,rtol=0)
            for k in range(2):
                c=lbm.C[:,k,None,None]
                np.testing.assert_allclose((post*c).sum(axis=0),(initial*c).sum(axis=0),atol=2e-15,rtol=0)

    def test_equal_end_flux_does_not_imply_local_continuity(self):
        # Analytic counterexample: endpoint flux agrees exactly, interior divergence does not.
        with tempfile.TemporaryDirectory() as tmp:
            x=np.linspace(0,22,177); y=np.linspace(0,4.1,34)
            xx,yy=np.meshgrid(x,y)
            u=6*yy*(4.1-yy)/4.1**2*(1+0.1*np.sin(2*np.pi*xx/22))
            v=np.zeros_like(u); solid=np.zeros_like(u,dtype=bool)
            solid[[0,-1],:]=True
            u[solid]=np.nan; v[solid]=np.nan
            path=Path(tmp)/"counterexample.npz"
            np.savez(path,x=x,y=y,u=u,v=v,p=np.where(solid,np.nan,0),solid=solid)
            result=diagnose(path)
            self.assertAlmostEqual(result["volume_flux_in"],result["volume_flux_out"],places=12)
            self.assertGreater(result["max_section_volume_flux_relative_departure"],0.09)
            self.assertGreater(result["divergence"]["all_valid"]["rms"],0.01)


    def test_density_weighted_flux_difference_does_not_require_absolute_density(self):
        with tempfile.TemporaryDirectory() as tmp:
            x=np.linspace(0,22,177); y=np.linspace(0,4.1,34)
            xx,yy=np.meshgrid(x,y)
            u=6*yy*(4.1-yy)/4.1**2; v=np.zeros_like(u)
            solid=np.zeros_like(u,dtype=bool); solid[[0,-1],:]=True
            u[solid]=np.nan; v[solid]=np.nan
            p=np.where(solid,np.nan,2*(1-xx/22))
            path=Path(tmp)/"mass_current.npz"
            results=[]
            for gauge in (0.0,7.0):
                np.savez(path,x=x,y=y,u=u,v=v,p=p+gauge,solid=solid)
                results.append(diagnose(path))
            expected=3*0.05**3*2*float(np.nansum(u[:,0]))
            for r in results:
                self.assertAlmostEqual(r["in_minus_out_density_weighted_flux_lattice"],expected,places=13)
            self.assertAlmostEqual(results[0]["mass_flux_difference_over_inlet_volume_flux"],
                                   3*0.05**2*2,places=13)

class SavedReferenceEvidenceTests(unittest.TestCase):
    def test_saved_histories_stop_at_first_four_consecutive_passing_checks(self):
        for relative in ("reference/cylinder_re10.json",
                         "grid_check/coarse/reference/cylinder_re10.json"):
            path=Path("project3_results")/relative
            if not path.exists():
                self.skipTest("Saved production metadata is not present")
            data=json.loads(path.read_text(encoding="utf-8"))
            cfg=data["config"]; streak=0; first=None
            for row in data["history"]:
                good=(row["step"]>=cfg["min_steps"] and
                      row["velocity_change"]<cfg["convergence_tolerance"])
                streak=streak+1 if good else 0
                if streak>=cfg["consecutive_convergence_checks"]:
                    first=row["step"]; break
            self.assertTrue(data["converged"])
            self.assertEqual(first,data["steps"])
            self.assertAlmostEqual(data["tau"],0.5+3*cfg["lattice_mean_velocity"]*
                                   cfg["nodes_per_diameter"]/data["reynolds"])
            # Equality already holds during large transients: it cannot certify convergence.
            self.assertGreater(data["history"][0]["velocity_change"],0.1)
            self.assertLess(data["history"][0]["mass_imbalance"],1e-12)

if __name__=="__main__":
    unittest.main()

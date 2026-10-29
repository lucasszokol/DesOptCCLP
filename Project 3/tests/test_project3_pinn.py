import csv
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from project3_pinn.config import ExperimentConfig, LBMConfig, PINNConfig
from project3_pinn.analysis import _external_lbm_validation, generate_analysis
from project3_pinn.geometry import LOSS_NAMES, is_inside_cylinder, sample_training_points
from project3_pinn.lbm import equilibrium, run_lbm
from project3_pinn.pinn import gradient_diagnostics, train_model, update_adaptive_weights


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.config = ExperimentConfig.quick()

    def test_interior_points_exclude_cylinder(self):
        points = sample_training_points(self.config.geometry, self.config.pinn, seed=7)
        self.assertFalse(np.any(is_inside_cylinder(points.interior, self.config.geometry)))

    def test_sampling_is_deterministic(self):
        first = sample_training_points(self.config.geometry, self.config.pinn, seed=9)
        second = sample_training_points(self.config.geometry, self.config.pinn, seed=9)
        np.testing.assert_array_equal(first.interior, second.interior)
        np.testing.assert_array_equal(first.walls, second.walls)

    def test_boundary_groups_have_expected_locations(self):
        points = sample_training_points(self.config.geometry, self.config.pinn, seed=1)
        self.assertTrue(np.all(points.inlet[:, 0] == 0.0))
        self.assertTrue(np.all(points.outlet[:, 0] == self.config.geometry.length))
        radius = np.sqrt(
            (points.walls[:, 0] - self.config.geometry.cylinder_x) ** 2
            + (points.walls[:, 1] - self.config.geometry.cylinder_y) ** 2
        )
        self.assertTrue(np.any(np.isclose(radius, self.config.geometry.cylinder_radius, atol=1e-5)))


class WeightingTests(unittest.TestCase):
    def test_weights_are_finite_bounded_and_normalized(self):
        config = ExperimentConfig.quick()
        weights = {name: 1.0 for name in LOSS_NAMES}
        norms = {name: 10.0 ** index for index, name in enumerate(LOSS_NAMES)}
        updated = update_adaptive_weights(weights, norms, config)
        values = np.array(list(updated.values()))
        self.assertTrue(np.all(np.isfinite(values)))
        self.assertAlmostEqual(float(np.mean(values)), 1.0, places=12)
        self.assertGreaterEqual(float(np.min(values)), config.pinn.min_weight)
        self.assertLessEqual(float(np.max(values)), config.pinn.max_weight)

    def test_extreme_repeated_updates_remain_strictly_bounded(self):
        config = ExperimentConfig.quick()
        weights = {name: 1.0 for name in LOSS_NAMES}
        norms = dict(zip(LOSS_NAMES, (1e-30, 1e-20, 1e-10, 1.0, 1e10, 1e30)))
        for _ in range(100):
            weights = update_adaptive_weights(weights, norms, config)
        values = np.array(list(weights.values()))
        self.assertAlmostEqual(float(np.mean(values)), 1.0, places=12)
        self.assertGreaterEqual(float(np.min(values)), config.pinn.min_weight)
        self.assertLessEqual(float(np.max(values)), config.pinn.max_weight)


class DiagnosticTests(unittest.TestCase):
    @unittest.skipUnless(__import__("importlib").util.find_spec("torch"), "PyTorch is not installed")
    def test_all_fifteen_named_gradient_cosines_are_returned(self):
        import torch

        model = torch.nn.Linear(2, 1)
        x = torch.tensor([[1.0, 2.0], [2.0, -1.0]])
        output = model(x)
        losses = {
            name: torch.mean((output - float(index + 1)) ** 2)
            for index, name in enumerate(LOSS_NAMES)
        }
        norms, cosines = gradient_diagnostics(losses, model)
        self.assertEqual(set(norms), set(LOSS_NAMES))
        self.assertEqual(len(cosines), 15)
        self.assertIn("continuity__momentum_x", cosines)

    def test_failed_run_writes_machine_readable_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = ExperimentConfig.quick(Path(temporary))
            with self.assertRaises(ValueError):
                train_model(config, reynolds=10, seed=0, method="invalid")
            failure = Path(temporary) / "runs" / "re10_invalid_seed0" / "failure.json"
            self.assertTrue(failure.exists())
            payload = json.loads(failure.read_text(encoding="utf-8"))
            self.assertEqual(payload["exception_type"], "ValueError")


class AnalysisTests(unittest.TestCase):
    def test_external_lbm_validation_uses_dfg_pressure_scaling(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = ExperimentConfig(output_dir=root)
            reference_dir = root / "reference"
            reference_dir.mkdir(parents=True)
            x = np.array([0.0, 1.5, 2.0, 2.5, 22.0])
            y = np.array([0.0, 2.0, 4.1])
            solid = np.zeros((3, 5), dtype=bool)
            solid[1, 2] = True
            pressure = np.zeros((3, 5))
            benchmark_pressure = 0.11752016697 / 0.2**2
            pressure[1, 1] = benchmark_pressure
            np.savez_compressed(
                reference_dir / "cylinder_re20.npz",
                x=x,
                y=y,
                u=np.zeros_like(pressure),
                v=np.zeros_like(pressure),
                p=pressure,
                solid=solid,
            )
            (reference_dir / "cylinder_re20.json").write_text(
                json.dumps({"drag_coefficient": 5.57953523384}), encoding="utf-8"
            )

            result = _external_lbm_validation(config)

            self.assertIsNotNone(result)
            self.assertAlmostEqual(result["drag_coefficient"]["relative_difference"], 0.0)
            self.assertAlmostEqual(result["pressure_difference"]["relative_difference"], 0.0)
            self.assertFalse(result["outlet_condition_match"])
            self.assertTrue((root / "analysis" / "lbm_external_validation.json").exists())

    def test_saved_lbm_drag_and_pressure_are_within_ten_percent_of_dfg(self):
        result = _external_lbm_validation(
            ExperimentConfig(output_dir=Path("project3_results"))
        )
        if result is None:
            self.skipTest("Saved Re=20 production reference is not present")
        self.assertLess(result["drag_coefficient"]["relative_difference"], 0.10)
        self.assertLess(result["pressure_difference"]["relative_difference"], 0.10)

    def test_all_five_report_figures_regenerate_from_saved_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = ExperimentConfig.quick(root)
            reference_dir = root / "reference"
            reference_dir.mkdir(parents=True)
            x = np.linspace(0.0, config.geometry.length, 8)
            y = np.linspace(0.0, config.geometry.height, 5)
            xx, yy = np.meshgrid(x, y)
            solid = np.zeros_like(xx, dtype=bool)
            u = np.broadcast_to(6 * yy * (config.geometry.height - yy) / config.geometry.height**2, xx.shape)
            v = np.zeros_like(u)
            p = 1.0 - xx / config.geometry.length
            np.savez_compressed(reference_dir / "cylinder_re10.npz", x=x, y=y, u=u, v=v, p=p, solid=solid)
            (reference_dir / "cylinder_re10.json").write_text(json.dumps({
                "runtime_seconds": 1.0,
                "reference_adequate": True,
                "history": [{"step": 1, "velocity_change": 1e-4, "mass_imbalance": 1e-5}],
            }), encoding="utf-8")
            analysis_dir = root / "analysis"
            analysis_dir.mkdir()
            (analysis_dir / "lbm_grid_refinement.json").write_text(
                json.dumps({"grid_adequate": True}), encoding="utf-8"
            )
            for method in config.methods:
                run_dir = root / "runs" / f"re10_{method}_seed0"
                run_dir.mkdir(parents=True)
                evaluation = {
                    "method": method, "reynolds": 10, "seed": 0,
                    "velocity_relative_l2": 0.2, "pressure_relative_l2": 0.3,
                    "divergence_rms": 0.01, "wall_velocity_rms": 0.01,
                    "drag_coefficient": 1.0, "recirculation_length": 0.1,
                    "inference_seconds": 0.01, "evaluation_points": int(u.size),
                }
                (run_dir / "evaluation.json").write_text(json.dumps(evaluation), encoding="utf-8")
                (run_dir / "training.json").write_text(json.dumps({"training_seconds": 1.0}), encoding="utf-8")
                if method != "supervised":
                    row = {"step": 1, "total": 1.0, "cosine_min": -0.5, "cosine_mean": 0.1}
                    for name in LOSS_NAMES:
                        row[f"loss_{name}"] = 1.0
                        row[f"weight_{name}"] = 1.0
                        row[f"grad_{name}"] = 1.0
                    with (run_dir / "history.csv").open("w", newline="", encoding="utf-8") as handle:
                        writer = csv.DictWriter(handle, fieldnames=list(row))
                        writer.writeheader()
                        writer.writerow(row)
                np.savez_compressed(
                    run_dir / "evaluation_fields.npz",
                    pred_u=u, pred_v=v, pred_p=p, error_speed=np.full_like(u, 0.01),
                )
            generated = generate_analysis(config)
            self.assertEqual(len(generated["figures"]), 5)
            self.assertTrue(all(Path(path).exists() for path in generated["figures"]))
            self.assertTrue(generated["decision"]["references_adequate"])


class LBMTests(unittest.TestCase):
    def test_equilibrium_recovers_density_and_velocity(self):
        rho = np.ones((3, 4))
        ux = np.full((3, 4), 0.03)
        uy = np.full((3, 4), -0.01)
        distribution = equilibrium(rho, ux, uy)
        np.testing.assert_allclose(np.sum(distribution, axis=0), rho, atol=1e-12)
        recovered_x = np.sum(distribution * np.array([0, 1, 0, -1, 0, 1, -1, -1, 1])[:, None, None], axis=0)
        recovered_y = np.sum(distribution * np.array([0, 0, 1, 0, -1, 1, 1, -1, -1])[:, None, None], axis=0)
        np.testing.assert_allclose(recovered_x, ux, atol=1e-12)
        np.testing.assert_allclose(recovered_y, uy, atol=1e-12)

    def test_short_reference_run_writes_finite_fluid_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = ExperimentConfig.quick(Path(temporary))
            config = replace(
                config,
                lbm=LBMConfig(
                    nodes_per_diameter=6,
                    lattice_mean_velocity=0.04,
                    max_steps=12,
                    min_steps=12,
                    check_every=6,
                    convergence_tolerance=0.0,
                ),
            )
            path = run_lbm(config, reynolds=10)
            with np.load(path) as data:
                fluid = ~data["solid"]
                self.assertTrue(np.all(np.isfinite(data["u"][fluid])))
                self.assertTrue(np.all(np.isfinite(data["v"][fluid])))
            metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["steps"], 12)
            self.assertGreater(metadata["tau"], 0.515)
            self.assertIn("mass_imbalance", metadata)
            self.assertIn("reference_adequate", metadata)
            self.assertFalse(metadata["reference_adequate"])


class AutodiffTests(unittest.TestCase):
    @unittest.skipUnless(__import__("importlib").util.find_spec("torch"), "PyTorch is not installed")
    def test_manufactured_field_has_expected_pde_residual(self):
        import torch

        from project3_pinn.pinn import navier_stokes_residual

        class ManufacturedField(torch.nn.Module):
            def forward(self, xy):
                x = xy[:, 0:1]
                y = xy[:, 1:2]
                return torch.cat((x**2, y**2, x + y), dim=1)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        xy = torch.rand(16, 2, device=device, requires_grad=True)
        model = ManufacturedField().to(device)
        _, continuity, momentum_x, momentum_y = navier_stokes_residual(model, xy, 20.0)
        x = xy[:, 0:1]
        y = xy[:, 1:2]
        torch.testing.assert_close(continuity, 2.0 * x + 2.0 * y)
        torch.testing.assert_close(momentum_x, 2.0 * x**3 + 1.0 - 2.0 / 20.0)
        torch.testing.assert_close(momentum_y, 2.0 * y**3 + 1.0 - 2.0 / 20.0)


if __name__ == "__main__":
    unittest.main()

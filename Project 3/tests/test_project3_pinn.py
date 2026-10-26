import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from project3_pinn.config import ExperimentConfig, LBMConfig, PINNConfig
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

"""Automated checks for the configurable truss and optimization study."""

import inspect
import unittest

import numpy as np

from project2_truss import (
    analyze_ratios,
    assemble_stiffness,
    condition_numbers,
    conjugate_gradient,
    create_truss_model,
    jacobi_rescaled_matrix,
    reduce_system,
    solve_displacement,
)
from truss_config import LOADS, MEMBERS, NODES, SUPPORTS


class TrussStudyTests(unittest.TestCase):
    """Check model input, assembly, the D2 diagnostic, and the solvers."""

    def setUp(self) -> None:
        """Create the documented 14-node example before each test."""

        self.model = create_truss_model(NODES, MEMBERS, SUPPORTS, LOADS)

    def test_custom_three_node_configuration(self) -> None:
        """Readable lists must create the expected degrees of freedom and loads."""

        nodes = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.5)]
        members = [(0, 1, "stiff"), (0, 2, "soft"), (1, 2, "stiff")]
        supports = [(0, True, True), (1, True, True)]
        loads = [(2, 2.0, -3.0)]

        model = create_truss_model(nodes, members, supports, loads)

        self.assertEqual(model.coordinates.shape, (3, 2))
        self.assertEqual(len(model.members), 3)
        np.testing.assert_array_equal(model.fixed_dofs, [0, 1, 2, 3])
        np.testing.assert_allclose(model.load, [0.0, 0.0, 0.0, 0.0, 2.0, -3.0])

    def test_invalid_configuration_is_rejected(self) -> None:
        """Bad node references, member data, and supports must fail clearly."""

        base_nodes = [(0.0, 0.0), (1.0, 0.0)]
        supports = [(0, True, True)]
        loads = [(1, 0.0, -1.0)]

        with self.assertRaisesRegex(ValueError, "unknown node"):
            create_truss_model(base_nodes, [(0, 2, "soft")], supports, loads)
        with self.assertRaisesRegex(ValueError, "zero length"):
            create_truss_model(
                [(0.0, 0.0), (0.0, 0.0)], [(0, 1, "soft")], supports, loads
            )
        with self.assertRaisesRegex(ValueError, "soft.*stiff"):
            create_truss_model(base_nodes, [(0, 1, "medium")], supports, loads)
        with self.assertRaisesRegex(ValueError, "SUPPORTS"):
            create_truss_model(base_nodes, [(0, 1, "soft")], [], loads)

    def test_unsupported_system_is_rejected(self) -> None:
        """A free vertical mechanism must fail the positive-definite check."""

        model = create_truss_model(
            [(0.0, 0.0), (1.0, 0.0)],
            [(0, 1, "soft")],
            [(0, True, True)],
            [(1, 0.0, -1.0)],
        )
        stiffness = assemble_stiffness(model, 10.0)
        reduced_stiffness, _, _ = reduce_system(model, stiffness)

        with self.assertRaisesRegex(ValueError, "positive definite"):
            condition_numbers(reduced_stiffness)

    def test_assembly_is_symmetric_and_reduced_matrix_is_positive_definite(self) -> None:
        """The finite element assembly must produce a valid quadratic Hessian."""

        stiffness = assemble_stiffness(self.model, 100.0)
        reduced_stiffness, _, _ = reduce_system(self.model, stiffness)

        np.testing.assert_allclose(stiffness, stiffness.T, atol=1.0e-13)
        np.testing.assert_allclose(reduced_stiffness, reduced_stiffness.T, atol=1.0e-13)
        self.assertGreater(np.linalg.eigvalsh(reduced_stiffness)[0], 0.0)

    def test_jacobi_rescaling_is_a_conditioning_diagnostic(self) -> None:
        """The D2 matrix must have a unit diagonal and need no load vector."""

        stiffness = assemble_stiffness(self.model, 100.0)
        reduced_stiffness, _, _ = reduce_system(self.model, stiffness)
        scaled_stiffness = jacobi_rescaled_matrix(reduced_stiffness)

        np.testing.assert_allclose(np.diag(scaled_stiffness), 1.0, atol=1.0e-13)
        self.assertEqual(list(inspect.signature(jacobi_rescaled_matrix).parameters), ["stiffness"])

    def test_ordinary_cg_solves_the_original_system(self) -> None:
        """Traditional CG must match the direct solution of the original system."""

        stiffness = assemble_stiffness(self.model, 100.0)
        reduced_stiffness, reduced_load, _ = reduce_system(self.model, stiffness)
        direct_solution = np.linalg.solve(reduced_stiffness, reduced_load)

        cg_solution, _, _ = conjugate_gradient(
            reduced_stiffness, reduced_load, tolerance=1.0e-12
        )

        np.testing.assert_allclose(cg_solution, direct_solution, rtol=1.0e-9)

    def test_saved_displacement_form_reinserts_fixed_dofs(self) -> None:
        """Full u must contain every node and zero displacement at supports."""

        full_u, reduced_u, free_dofs = solve_displacement(self.model, 10000.0)
        stiffness = assemble_stiffness(self.model, 10000.0)
        reduced_stiffness, reduced_load, expected_free_dofs = reduce_system(
            self.model, stiffness
        )

        self.assertEqual(full_u.shape, (2 * len(self.model.coordinates),))
        np.testing.assert_array_equal(free_dofs, expected_free_dofs)
        np.testing.assert_allclose(full_u[self.model.fixed_dofs], 0.0)
        np.testing.assert_allclose(full_u[free_dofs], reduced_u)
        np.testing.assert_allclose(
            reduced_stiffness @ reduced_u, reduced_load, rtol=1.0e-10, atol=1.0e-10
        )

    def test_cg_has_no_preconditioner_interface_or_residual_scaling(self) -> None:
        """Jacobi operations must remain outside the ordinary CG implementation."""

        signature = inspect.signature(conjugate_gradient)
        source = inspect.getsource(conjugate_gradient)

        self.assertEqual(
            list(signature.parameters),
            ["stiffness", "load", "tolerance", "maximum_iterations"],
        )
        self.assertNotIn("preconditioner", source.lower())
        self.assertNotIn("inverse_diagonal", source)
        self.assertNotIn("scale_factors", source)

    def test_condition_numbers_grow_and_rescaling_does_not_remove_growth(self) -> None:
        """The stiffness contrast must remain an intrinsic conditioning problem."""

        original = []
        scaled = []
        for ratio in [1.0, 10.0, 100.0, 1000.0, 10000.0]:
            stiffness = assemble_stiffness(self.model, ratio)
            reduced_stiffness, _, _ = reduce_system(self.model, stiffness)
            original_condition, scaled_condition, _, _ = condition_numbers(
                reduced_stiffness
            )
            original.append(original_condition)
            scaled.append(scaled_condition)

        self.assertTrue(np.all(np.diff(original) > 0.0))
        self.assertGreater(original[-1] / original[0], 100.0)
        self.assertGreater(scaled[-1] / scaled[0], 100.0)
        self.assertGreater(scaled[-1], 1000.0)

    def test_d4_methods_use_the_same_energy_tolerance(self) -> None:
        """Traditional CG must beat GD at the shared physical error target."""

        record = analyze_ratios(self.model, np.array([10000.0]))[0]

        self.assertIsNotNone(record["gd_iterations_energy_tolerance"])
        self.assertIsNotNone(record["cg_iterations_energy_tolerance"])
        self.assertLess(
            record["cg_iterations_energy_tolerance"],
            record["gd_iterations_energy_tolerance"],
        )
        self.assertLessEqual(record["cg_final_relative_energy_gap"], 1.0e-8)
        self.assertGreater(record["cg_iteration_speedup"], 1.0)


if __name__ == "__main__":
    unittest.main()

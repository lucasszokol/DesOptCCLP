"""Finite element and optimization study for an ill-conditioned aircraft spar.

Running this file creates every figure and numerical result used by the report.
Only NumPy and Matplotlib are required.
"""

# Delay the evaluation of type hints so modern annotations remain portable.
from __future__ import annotations

# Write the diagnostic table in a format that spreadsheet software can read.
import csv
# Write the model verification results as structured text.
import json
# A dataclass groups related model arrays without a custom constructor.
from dataclasses import dataclass
# Path creates file locations that work on Windows, macOS, and Linux.
from pathlib import Path

# Matplotlib creates figures, and NumPy performs the matrix calculations.
import matplotlib
import numpy as np

# The Agg backend writes image files without opening a desktop window.
matplotlib.use("Agg")
# Import pyplot only after selecting the noninteractive backend.
import matplotlib.pyplot as plt

# The example geometry lives in a separate file that students can edit.
from truss_config import LOADS, MEMBERS, NODES, SUPPORTS


# Store numerical tables beside this script in the results directory.
OUTPUT_DIR = Path(__file__).resolve().parent / "results"
# Store report images beside this script in the figures directory.
FIGURE_DIR = Path(__file__).resolve().parent / "figures"
# One configuration coordinate unit becomes 1000 mm in the ANSYS comparison.
ANSYS_COORDINATE_SCALE_MM = 1000.0
# A typical steel modulus gives practical areas while preserving each exact k.
ANSYS_YOUNGS_MODULUS_MPA = 200000.0


# frozen=True prevents accidental replacement of model data after creation.
@dataclass(frozen=True)
class TrussModel:
    """Store all geometry, connectivity, support, and load data for one truss."""

    # Each row contains the x and y coordinates of one node.
    coordinates: np.ndarray
    # Each member stores its start node, end node, and stiffness group.
    members: tuple[tuple[int, int, str], ...]
    # Fixed degrees of freedom have prescribed zero displacement.
    fixed_dofs: np.ndarray
    # The load vector stores horizontal and vertical force at every node.
    load: np.ndarray


def create_truss_model(
    nodes: list[tuple[float, float]],
    members: list[tuple[int, int, str]],
    supports: list[tuple[int, bool, bool]],
    loads: list[tuple[int, float, float]],
) -> TrussModel:
    """Validate readable input lists and convert them to analysis arrays."""

    # Convert node coordinates to a two-column floating-point array.
    coordinates = np.asarray(nodes, dtype=float)
    # A valid 2D model needs at least two finite x-y coordinate pairs.
    if coordinates.ndim != 2 or coordinates.shape[1] != 2 or len(coordinates) < 2:
        raise ValueError("NODES must contain at least two (x, y) coordinate pairs.")
    if not np.all(np.isfinite(coordinates)):
        raise ValueError("Every node coordinate must be finite.")

    # A model with no members cannot transfer load between nodes.
    if not members:
        raise ValueError("MEMBERS must contain at least one truss member.")
    validated_members: list[tuple[int, int, str]] = []
    for member_index, (node_i, node_j, group) in enumerate(members):
        # Node references must be integer positions in the NODES list.
        if not isinstance(node_i, (int, np.integer)) or not isinstance(
            node_j, (int, np.integer)
        ):
            raise ValueError(f"Member {member_index} node references must be integers.")
        # Both endpoint numbers must select existing rows in NODES.
        if not 0 <= node_i < len(coordinates) or not 0 <= node_j < len(coordinates):
            raise ValueError(f"Member {member_index} refers to an unknown node.")
        # Only the two project stiffness groups are supported.
        if group not in {"soft", "stiff"}:
            raise ValueError(f"Member {member_index} must use group 'soft' or 'stiff'.")
        # Coincident endpoint coordinates create a zero-length member.
        if np.linalg.norm(coordinates[node_j] - coordinates[node_i]) <= 0.0:
            raise ValueError(f"Member {member_index} has zero length.")
        validated_members.append((int(node_i), int(node_j), group))

    # At least one constrained displacement is required to reduce rigid motion.
    if not supports:
        raise ValueError("SUPPORTS must constrain at least one displacement.")
    fixed_dofs: list[int] = []
    for node, fix_x, fix_y in supports:
        # A node reference such as 2.5 cannot identify one row of NODES.
        if not isinstance(node, (int, np.integer)):
            raise ValueError("Support node references must be integers.")
        # A support node must select an existing row in NODES.
        if not 0 <= node < len(coordinates):
            raise ValueError(f"Support refers to unknown node {node}.")
        # Horizontal displacement u_x is stored at global index 2*node.
        if fix_x:
            fixed_dofs.append(2 * node)
        # Vertical displacement u_y is stored at global index 2*node+1.
        if fix_y:
            fixed_dofs.append(2 * node + 1)
    # Reject a support list that does not actually constrain any displacement.
    if not fixed_dofs:
        raise ValueError("SUPPORTS must fix at least one displacement component.")

    # Start with zero horizontal and vertical force at every node.
    load_vector = np.zeros(2 * len(coordinates))
    for node, force_x, force_y in loads:
        # Loads also use zero-based integer positions in the NODES list.
        if not isinstance(node, (int, np.integer)):
            raise ValueError("Load node references must be integers.")
        # A loaded node must select an existing row in NODES.
        if not 0 <= node < len(coordinates):
            raise ValueError(f"Load refers to unknown node {node}.")
        # NaN and infinite forces are not physical model inputs.
        if not np.isfinite(force_x) or not np.isfinite(force_y):
            raise ValueError(f"Load at node {node} must contain finite values.")
        # Add loads so more than one load entry can act on the same node.
        load_vector[2 * node] += force_x
        load_vector[2 * node + 1] += force_y
    # A zero load makes the optimization problem trivial and breaks relative errors.
    if not np.any(load_vector):
        raise ValueError("LOADS must contain at least one nonzero force component.")

    # Remove duplicate support entries and store them in ascending order.
    fixed_dof_array = np.unique(np.asarray(fixed_dofs, dtype=int))
    # Return one immutable model object for assembly, plotting, and diagnostics.
    return TrussModel(
        coordinates=coordinates,
        members=tuple(validated_members),
        fixed_dofs=fixed_dof_array,
        load=load_vector,
    )


def element_stiffness(
    point_i: np.ndarray, point_j: np.ndarray, member_stiffness: float
) -> np.ndarray:
    """Return the 4-by-4 global-coordinate stiffness matrix for one 2D truss member."""
    # The coordinate difference gives the member direction and length.
    delta = point_j - point_i
    length = float(np.linalg.norm(delta))
    # A zero-length member has no direction and would cause division by zero.
    if length <= 0.0:
        raise ValueError("A truss member must have nonzero length.")
    # Dividing by length gives the direction cosine c and direction sine s.
    cosine, sine = delta / length
    # This matrix rotates the axial member response into global x-y coordinates.
    direction_matrix = np.array(
        [
            [cosine**2, cosine * sine, -cosine**2, -cosine * sine],
            [cosine * sine, sine**2, -cosine * sine, -sine**2],
            [-cosine**2, -cosine * sine, cosine**2, cosine * sine],
            [-cosine * sine, -sine**2, cosine * sine, sine**2],
        ]
    )
    # The configured axial member stiffness k=EA/L multiplies this matrix.
    return member_stiffness * direction_matrix


def assemble_stiffness(
    model: TrussModel, stiffness_ratio: float, soft_member_stiffness: float = 1.0
) -> np.ndarray:
    """Assemble K using r = (EA/L)_stiff / (EA/L)_soft."""
    # The soft group defines the minimum stiffness, so r cannot be below one.
    if stiffness_ratio < 1.0:
        raise ValueError("The stiffness ratio must be at least one.")

    # Two displacement components per node determine the global matrix size.
    number_of_dofs = 2 * len(model.coordinates)
    # Begin with no member contributions in the global stiffness matrix.
    stiffness = np.zeros((number_of_dofs, number_of_dofs))
    for node_i, node_j, group in model.members:
        # Assign k=EA/L so that the stiff-to-soft ratio is exactly r.
        member_stiffness = soft_member_stiffness * (
            stiffness_ratio if group == "stiff" else 1.0
        )
        # Calculate this member's 4-by-4 matrix in global coordinates.
        member_matrix = element_stiffness(
            model.coordinates[node_i], model.coordinates[node_j], member_stiffness
        )
        # Map local order [ix, iy, jx, jy] to global matrix row and column numbers.
        dofs = np.array(
            [2 * node_i, 2 * node_i + 1, 2 * node_j, 2 * node_j + 1], dtype=int
        )
        # Add the member matrix because connected members share global entries.
        stiffness[np.ix_(dofs, dofs)] += member_matrix
    # Return the full matrix before support conditions are applied.
    return stiffness


def reduce_system(model: TrussModel, stiffness: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Remove fixed displacement coordinates and return K, f, and the free DOF indices."""
    # List every displacement index in the unreduced system.
    all_dofs = np.arange(stiffness.shape[0])
    # Keep only displacement indices that are not fixed at the root.
    free_dofs = np.setdiff1d(all_dofs, model.fixed_dofs)
    # Select free rows and columns to impose zero root displacement.
    reduced_stiffness = stiffness[np.ix_(free_dofs, free_dofs)]
    # Remove force entries that correspond to fixed displacement coordinates.
    reduced_load = model.load[free_dofs]
    # The free index list can later expand a reduced solution if needed.
    return reduced_stiffness, reduced_load, free_dofs


def potential_energy(displacement: np.ndarray, stiffness: np.ndarray, load: np.ndarray) -> float:
    """Evaluate strain energy minus external work for one displacement vector."""

    # The @ operator performs matrix-vector and vector-vector multiplication.
    return float(0.5 * displacement @ stiffness @ displacement - load @ displacement)


def jacobi_rescaled_matrix(stiffness: np.ndarray) -> np.ndarray:
    """Return D^(-1/2) K D^(-1/2) for the required D2 diagnostic."""

    # The diagnostic requires a square stiffness matrix.
    if stiffness.ndim != 2 or stiffness.shape[0] != stiffness.shape[1]:
        raise ValueError("The stiffness matrix must be square.")
    # D=diag(K) contains one coordinate stiffness for each unknown displacement.
    diagonal = np.diag(stiffness)
    # Positive entries are required to calculate the real-valued inverse square root.
    if np.any(diagonal <= 0.0):
        raise ValueError("Jacobi rescaling requires positive diagonal entries.")
    # These are the diagonal entries of D^(-1/2).
    scale_factors = 1.0 / np.sqrt(diagonal)
    # Scale rows and columns without constructing a dense diagonal matrix.
    return stiffness * np.outer(scale_factors, scale_factors)


def condition_numbers(stiffness: np.ndarray) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Return original and Jacobi-rescaled condition numbers and spectra."""
    # eigvalsh returns real eigenvalues in ascending order for a symmetric matrix.
    eigenvalues = np.linalg.eigvalsh(stiffness)
    # Positive eigenvalues are required for the energy minimization and CG.
    if eigenvalues[0] <= 0.0:
        raise ValueError("The reduced stiffness matrix must be positive definite.")
    # Jacobi rescaling is used only for the required intrinsic-conditioning test.
    scaled_stiffness = jacobi_rescaled_matrix(stiffness)
    # Compute the spectrum of the explicitly rescaled matrix.
    scaled_eigenvalues = np.linalg.eigvalsh(scaled_stiffness)
    # For a positive definite matrix, kappa is largest eigenvalue / smallest.
    condition_number = float(eigenvalues[-1] / eigenvalues[0])
    scaled_condition_number = float(scaled_eigenvalues[-1] / scaled_eigenvalues[0])
    # Return both summary values and both spectra for the D1-D2 figures.
    return condition_number, scaled_condition_number, eigenvalues, scaled_eigenvalues


def gradient_descent_diagnostics(
    stiffness: np.ndarray,
    load: np.ndarray,
    sample_iterations: np.ndarray,
    tolerance: float = 1.0e-8,
    maximum_iterations: int = 1_000_000_000,
) -> tuple[float, np.ndarray, int | None]:
    """Evaluate fixed-step gradient descent exactly in the Hessian eigenbasis.

    The step size 2/(lambda_max + lambda_min) is the best constant step size
    when only the smallest and largest eigenvalues are used. Spectral evaluation
    avoids millions of slow Python loop iterations but gives the same iterates,
    up to floating-point roundoff, as the recurrence u[k+1] = u[k]-alpha grad Pi.
    """
    # eigh returns both eigenvalues and orthonormal eigenvectors of K.
    eigenvalues, eigenvectors = np.linalg.eigh(stiffness)
    # This is the best fixed step for a positive definite quadratic when the
    # smallest and largest eigenvalues are known.
    alpha = 2.0 / (eigenvalues[0] + eigenvalues[-1])
    # The exact minimizer solves K u*=f and provides the reference error.
    optimum = np.linalg.solve(stiffness, load)
    # u0=0, so the initial displacement error is e0=u0-u*=-u*.
    # Multiplication by V^T expresses that error in eigenvector coordinates.
    initial_error_coordinates = eigenvectors.T @ (-optimum)
    # Each mode contributes lambda_i*c_i^2 to twice the energy error.
    energy_weights = eigenvalues * initial_error_coordinates**2
    # One gradient step multiplies eigenmode i by 1-alpha*lambda_i.
    contraction = np.abs(1.0 - alpha * eigenvalues)
    # The factor of one-half cancels when the energy error is normalized.
    initial_gap_twice = float(np.sum(energy_weights))

    def relative_gap(iteration: int | np.ndarray) -> np.ndarray:
        """Evaluate the exact relative energy error at selected iterations."""

        # Convert one integer or an integer array to a consistent array shape.
        iteration_array = np.atleast_1d(iteration).astype(np.int64)
        # Energy is quadratic, so each modal contraction is raised to 2k.
        powers = np.power(contraction[None, :], 2 * iteration_array[:, None])
        # Sum all modal energy contributions and divide by the initial value.
        return (powers @ energy_weights) / initial_gap_twice

    # Produce values for the iteration numbers requested by a plot or table.
    sampled_gap = relative_gap(sample_iterations)
    # Report no convergence if even the allowed maximum misses the tolerance.
    if relative_gap(maximum_iterations)[0] > tolerance:
        iterations_to_tolerance = None
    else:
        # Binary search finds the first successful iteration without looping
        # through every gradient step.
        low, high = 0, maximum_iterations
        while low < high:
            middle = (low + high) // 2
            if relative_gap(middle)[0] <= tolerance:
                # The first successful iteration is at or before the midpoint.
                high = middle
            else:
                # The first successful iteration must be after the midpoint.
                low = middle + 1
        iterations_to_tolerance = low
    # Return the step size, sampled curve, and first successful iteration.
    return alpha, sampled_gap, iterations_to_tolerance


def conjugate_gradient(
    stiffness: np.ndarray,
    load: np.ndarray,
    tolerance: float = 1.0e-8,
    maximum_iterations: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve K u = f with traditional, unpreconditioned conjugate gradient."""

    # The vector length equals the number of unknown displacement components.
    number_of_dofs = len(load)
    # Exact arithmetic needs at most n steps. Extra steps allow for roundoff.
    maximum_iterations = maximum_iterations or 5 * number_of_dofs
    # Start from zero displacement so the initial residual equals the load.
    displacement = np.zeros_like(load)
    # r_k=f-Ku_k is both the force imbalance and the negative gradient.
    residual = load - stiffness @ displacement
    # Traditional CG uses the initial residual as its first search direction.
    direction = residual.copy()
    # Store r_k^T r_k because alpha and beta both use this value.
    residual_product = float(residual @ residual)
    # Save the initial norm so every later residual can be normalized.
    initial_residual_norm = float(np.linalg.norm(residual))
    # This direct solution is used only to measure energy error for the report.
    optimum = np.linalg.solve(stiffness, load)
    # For a quadratic, Pi(u)-Pi(u*)=0.5*(u-u*)^T K (u-u*).
    # This form avoids subtracting two nearly equal potential-energy values.
    initial_error = displacement - optimum
    initial_gap = float(0.5 * initial_error @ stiffness @ initial_error)
    # Both histories start at one because they are relative to initial values.
    gaps = [1.0]
    residual_norms = [1.0]

    # Repeat the standard CG recurrence until convergence or the safety limit.
    for _ in range(maximum_iterations):
        # q_k=Kp_k is the change in internal force along the search direction.
        stiffness_direction = stiffness @ direction
        # alpha_k=(r_k^T r_k)/(p_k^T K p_k) minimizes energy along p_k.
        step = residual_product / float(direction @ stiffness_direction)
        # Move the displacement estimate by alpha_k p_k.
        displacement = displacement + step * direction
        # Update the residual without recomputing f-Ku from the beginning.
        residual = residual - step * stiffness_direction
        # Use the positive quadratic error to measure physical energy accurately.
        displacement_error = displacement - optimum
        gap = float(0.5 * displacement_error @ stiffness @ displacement_error)
        # A tiny positive floor prevents roundoff from breaking logarithmic plots.
        gaps.append(max(float(gap / initial_gap), np.finfo(float).tiny))
        # Measure the remaining force imbalance relative to its initial value.
        relative_residual = float(np.linalg.norm(residual) / initial_residual_norm)
        residual_norms.append(relative_residual)
        # Stop when the force imbalance reaches the requested tolerance.
        if relative_residual <= tolerance:
            break
        # rho_(k+1)=r_(k+1)^T r_(k+1) is needed for the direction update.
        next_residual_product = float(residual @ residual)
        # beta_k=rho_(k+1)/rho_k makes the new direction K-conjugate.
        # p_(k+1)=r_(k+1)+beta_k*p_k keeps useful previous progress.
        direction = residual + (next_residual_product / residual_product) * direction
        # Save rho_(k+1) so it becomes rho_k in the next loop pass.
        residual_product = next_residual_product

    # Return the final displacement and both recorded convergence histories.
    return displacement, np.asarray(gaps), np.asarray(residual_norms)


def convergence_at_tolerance(
    relative_gaps: np.ndarray, tolerance: float = 1.0e-8
) -> tuple[int | None, float | None]:
    """Return the first successful iteration and its observed effective rate."""

    # Find all stored iterations whose relative energy error reaches the target.
    successful_iterations = np.flatnonzero(relative_gaps <= tolerance)
    # Return missing values if the recorded solver history never reaches the target.
    if len(successful_iterations) == 0:
        return None, None
    # The first matching array index is also the completed iteration count.
    iterations = int(successful_iterations[0])
    # rho_eff=(E_k/E_0)^(1/k) is average energy error retained per iteration.
    effective_rate = float(relative_gaps[iterations] ** (1.0 / iterations))
    return iterations, effective_rate


def analyze_ratios(model: TrussModel, ratios: np.ndarray) -> list[dict[str, float | int | None]]:
    """Run D1-D4 calculations for every requested stiffness ratio."""

    # Each dictionary becomes one row in the diagnostic CSV file.
    records: list[dict[str, float | int | None]] = []
    for ratio in ratios:
        # Assemble and reduce a new matrix because r changes member stiffnesses.
        stiffness_full = assemble_stiffness(model, float(ratio))
        stiffness, load, _ = reduce_system(model, stiffness_full)
        # D1-D2 require the original and diagonally rescaled condition numbers.
        condition_number, scaled_condition_number, _, _ = condition_numbers(stiffness)
        # First find the gradient-descent iteration that reaches 10^-8.
        _, _, gd_iterations = gradient_descent_diagnostics(
            stiffness, load, np.array([0], dtype=int)
        )
        if gd_iterations is None:
            # A missing iteration count means that no effective rate is defined.
            gd_effective_rate = None
        else:
            # Evaluate the energy error exactly at the first successful step.
            _, gd_hit_gap, _ = gradient_descent_diagnostics(
                stiffness, load, np.array([gd_iterations], dtype=int)
            )
            # rho_eff=(E_k/E_0)^(1/k) is average error retained per iteration.
            gd_effective_rate = float(gd_hit_gap[0] ** (1.0 / gd_iterations))
        # Run traditional CG on the same original K and f used by gradient descent.
        _, cg_gaps, cg_residuals = conjugate_gradient(stiffness, load)
        cg_iterations, cg_rate = convergence_at_tolerance(cg_gaps)
        # Compare CG with GD at the same relative potential-energy tolerance.
        cg_speedup = (
            float(gd_iterations / cg_iterations)
            if gd_iterations is not None and cg_iterations is not None
            else None
        )
        # Keep raw values so the report can round them without losing data.
        records.append(
            {
                "stiffness_ratio": int(ratio),
                "condition_number": condition_number,
                "scaled_condition_number": scaled_condition_number,
                "gd_iterations_energy_tolerance": gd_iterations,
                "cg_iterations_energy_tolerance": cg_iterations,
                "gd_effective_rate": gd_effective_rate,
                "cg_effective_rate": cg_rate,
                "cg_iteration_speedup": cg_speedup,
                "cg_iterations_residual_tolerance": len(cg_residuals) - 1,
                "cg_final_relative_energy_gap": float(cg_gaps[-1]),
            }
        )
    # Return all rows after the complete ratio sweep.
    return records


def verify_model(model: TrussModel) -> dict[str, float | bool]:
    """Run numerical checks that support the finite element and CG results."""

    # Use an intermediate stiffness ratio for the independent verification case.
    stiffness_full = assemble_stiffness(model, stiffness_ratio=100.0)
    stiffness, load, _ = reduce_system(model, stiffness_full)
    # Positive eigenvalues prove positive definiteness after boundary conditions.
    eigenvalues = np.linalg.eigvalsh(stiffness)
    # A direct linear solve supplies an independent reference displacement.
    direct_solution = np.linalg.solve(stiffness, load)
    # Use a tighter residual tolerance for the comparison with the direct solve.
    cg_solution, _, _ = conjugate_gradient(stiffness, load, tolerance=1.0e-10)
    # The gradient Ku-f must be nearly zero at the direct minimizer.
    gradient_at_solution = stiffness @ direct_solution - load
    # Store Boolean tests and normalized errors as JSON-compatible values.
    return {
        # Symmetry is required for the energy and conjugate-gradient formulas.
        "global_stiffness_is_symmetric": bool(np.allclose(stiffness_full, stiffness_full.T)),
        # This value shows the numerical distance from a zero eigenvalue.
        "smallest_reduced_eigenvalue": float(eigenvalues[0]),
        # A positive smallest eigenvalue means that every free mode has stiffness.
        "reduced_stiffness_is_positive_definite": bool(eigenvalues[0] > 0.0),
        # Normalize the equilibrium error so its magnitude is easy to interpret.
        "relative_gradient_norm_at_direct_solution": float(
            np.linalg.norm(gradient_at_solution) / np.linalg.norm(load)
        ),
        # Compare CG and direct displacements relative to the direct solution size.
        "relative_cg_solution_error": float(
            np.linalg.norm(cg_solution - direct_solution) / np.linalg.norm(direct_solution)
        ),
    }


def solve_displacement(
    model: TrussModel, stiffness_ratio: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve equilibrium and return full u, reduced u, and free DOF numbers."""

    # Assemble the full finite element matrix for the requested member ratio.
    stiffness_full = assemble_stiffness(model, stiffness_ratio)
    # Apply supports by selecting only the free displacement coordinates.
    stiffness, load, free_dofs = reduce_system(model, stiffness_full)
    # The unique energy-minimizing displacement solves K u=f.
    reduced_displacement = np.linalg.solve(stiffness, load)
    # Reinsert zeros at supported coordinates to create [u0x,u0y,u1x,u1y,...].
    full_displacement = np.zeros(2 * len(model.coordinates))
    full_displacement[free_dofs] = reduced_displacement
    # Keep both forms because the optimizer uses reduced u while plots use full u.
    return full_displacement, reduced_displacement, free_dofs


def plot_structure(model: TrussModel, path: Path) -> None:
    """Draw the truss geometry, groups, supports, node numbers, and tip load."""

    # Use a wide figure because the spar span is much larger than its height.
    fig, ax = plt.subplots(figsize=(11, 3.1))
    # Keep one consistent color for each member-stiffness group.
    colors = {"stiff": "#176B87", "soft": "#D1495B"}
    # Track legend labels so each group appears only once.
    labels_drawn: set[str] = set()
    for node_i, node_j, group in model.members:
        # Select the two endpoint coordinate rows for this member.
        points = model.coordinates[[node_i, node_j]]
        # The first member in each group creates that group's legend entry.
        label = f"{group.capitalize()} member group" if group not in labels_drawn else None
        # Draw a straight line between the two endpoint nodes.
        ax.plot(points[:, 0], points[:, 1], color=colors[group], linewidth=2.8, label=label)
        labels_drawn.add(group)
    # Draw every truss joint above the member lines.
    ax.scatter(model.coordinates[:, 0], model.coordinates[:, 1], s=24, color="#202124", zorder=3)
    # Convert fixed displacement indices back to the supported node numbers.
    supported_nodes = np.unique(model.fixed_dofs // 2)
    # Square markers identify every node that has at least one fixed component.
    ax.scatter(
        model.coordinates[supported_nodes, 0],
        model.coordinates[supported_nodes, 1],
        marker="s",
        s=90,
        facecolors="none",
        edgecolors="#4A4A4A",
        linewidths=2,
        label="Supported nodes",
    )
    # Use the geometry size to draw load arrows at a visible, consistent length.
    x_range = float(np.ptp(model.coordinates[:, 0]))
    y_range = float(np.ptp(model.coordinates[:, 1]))
    geometry_size = max(x_range, y_range, 1.0)
    arrow_length = 0.12 * geometry_size
    # Reshape the global load vector into one [Fx, Fy] row per node.
    nodal_loads = model.load.reshape((-1, 2))
    for node, force in enumerate(nodal_loads):
        # Skip nodes that have no applied force.
        force_magnitude = float(np.linalg.norm(force))
        if force_magnitude == 0.0:
            continue
        # Draw the arrow toward the loaded node in the force direction.
        force_direction = force / force_magnitude
        arrow_start = model.coordinates[node] - arrow_length * force_direction
        ax.annotate(
            "",
            xy=model.coordinates[node],
            xytext=arrow_start,
            arrowprops={"arrowstyle": "-|>", "color": "#111111", "lw": 2.0},
        )
    # Add one legend sample for all load arrows.
    ax.plot([], [], color="#111111", linewidth=2.0, label="Applied loads")
    # Print the node number slightly above and to the right of each joint.
    for node, (x, y) in enumerate(model.coordinates):
        ax.text(x + 0.04, y + 0.07, str(node), fontsize=8, color="#333333")
    # Equal axis scaling prevents the truss geometry from being distorted.
    ax.set_aspect("equal")
    # Add margins that adapt to a replacement geometry from truss_config.py.
    margin = 0.18 * geometry_size
    ax.set_xlim(model.coordinates[:, 0].min() - margin, model.coordinates[:, 0].max() + margin)
    ax.set_ylim(model.coordinates[:, 1].min() - margin, model.coordinates[:, 1].max() + margin)
    # Label the two geometric axes.
    ax.set_xlabel("Spanwise position")
    ax.set_ylabel("Spar height")
    # Place a compact legend below the truss and remove unused frame lines.
    ax.legend(loc="lower center", ncol=4, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    # Fit all labels, write a high-resolution image, and release the figure.
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_deformed_structure(
    model: TrussModel,
    full_displacement: np.ndarray,
    stiffness_ratio: float,
    path: Path,
) -> float:
    """Plot ANSYS-scale geometry with magnified displacement and return the scale."""

    # Convert the flat u vector into one [u_x,u_y] row for each node.
    nodal_displacement = full_displacement.reshape((-1, 2))
    # Use the same millimeter coordinates as the exported ANSYS model.
    original_coordinates = ANSYS_COORDINATE_SCALE_MM * model.coordinates
    # Use the largest node displacement to choose a visible plotting scale.
    displacement_magnitudes = np.linalg.norm(nodal_displacement, axis=1)
    maximum_displacement = float(np.max(displacement_magnitudes))
    # Match the ANSYS AUTO display seen here: maximum motion is 5% of the span.
    x_range = float(np.ptp(original_coordinates[:, 0]))
    y_range = float(np.ptp(original_coordinates[:, 1]))
    geometry_size = max(x_range, y_range, 1.0)
    deformation_scale = (
        0.05 * geometry_size / maximum_displacement
        if maximum_displacement > 0.0
        else 1.0
    )
    # ANSYS-style magnification affects only the picture, never the saved solution.
    deformed_coordinates = original_coordinates + deformation_scale * nodal_displacement

    # Draw the original shape as a dashed reference and the deformed shape by group.
    fig, ax = plt.subplots(figsize=(11, 3.8))
    colors = {"stiff": "#176B87", "soft": "#D1495B"}
    labels_drawn: set[str] = set()
    for node_i, node_j, group in model.members:
        original_points = original_coordinates[[node_i, node_j]]
        deformed_points = deformed_coordinates[[node_i, node_j]]
        # Only one original member creates the undeformed legend entry.
        original_label = "Undeformed" if "undeformed" not in labels_drawn else None
        ax.plot(
            original_points[:, 0],
            original_points[:, 1],
            color="#8A8A8A",
            linestyle="--",
            linewidth=1.2,
            label=original_label,
        )
        labels_drawn.add("undeformed")
        # The first deformed member in each group creates its legend entry.
        deformed_label = (
            f"Deformed {group} members" if group not in labels_drawn else None
        )
        ax.plot(
            deformed_points[:, 0],
            deformed_points[:, 1],
            color=colors[group],
            linewidth=2.6,
            label=deformed_label,
        )
        labels_drawn.add(group)
    # Mark undeformed and deformed node locations for direct visual comparison.
    ax.scatter(
        original_coordinates[:, 0],
        original_coordinates[:, 1],
        s=20,
        facecolors="white",
        edgecolors="#666666",
        zorder=3,
    )
    ax.scatter(
        deformed_coordinates[:, 0],
        deformed_coordinates[:, 1],
        s=24,
        color="#202124",
        zorder=4,
    )
    # Label the deformed nodes with the same zero-based numbers as truss_config.py.
    label_x_offset = 0.007 * geometry_size
    label_y_offset = 0.009 * geometry_size
    for node, (x_coordinate, y_coordinate) in enumerate(deformed_coordinates):
        ax.text(
            x_coordinate + label_x_offset,
            y_coordinate + label_y_offset,
            str(node),
            fontsize=8,
        )
    # Include both shapes when calculating plot limits.
    all_coordinates = np.vstack((original_coordinates, deformed_coordinates))
    margin = 0.12 * geometry_size
    ax.set_xlim(all_coordinates[:, 0].min() - margin, all_coordinates[:, 0].max() + margin)
    ax.set_ylim(all_coordinates[:, 1].min() - margin, all_coordinates[:, 1].max() + margin)
    ax.set_aspect("equal")
    ax.set_xlabel("Spanwise position (mm)")
    ax.set_ylabel("Spar height (mm)")
    ax.set_title(
        f"Equilibrium displacement at r = {stiffness_ratio:,.0f} "
        f"(displacement magnification = {deformation_scale:.3g}x)"
    )
    ax.legend(loc="best", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
    # Save this value with u so another person can reproduce the displayed shape.
    return deformation_scale


def plot_eigenvalue_spectrum(model: TrussModel, ratio: float, path: Path) -> None:
    """Create the D1 spectrum plot before and after diagonal rescaling."""

    # Build the reduced stiffness matrix for the selected ratio.
    stiffness, _, _ = reduce_system(model, assemble_stiffness(model, ratio))
    # Obtain sorted spectra for the original and explicitly rescaled matrices.
    _, _, eigenvalues, scaled_eigenvalues = condition_numbers(stiffness)
    # Number the eigenvalues from one for an undergraduate-readable x-axis.
    mode_numbers = np.arange(1, len(eigenvalues) + 1)
    # A logarithmic y-axis reveals both very small and very large eigenvalues.
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.semilogy(mode_numbers, eigenvalues, "o-", color="#176B87", label="Original stiffness matrix")
    ax.semilogy(
        mode_numbers,
        scaled_eigenvalues,
        "s-",
        color="#D1495B",
        label="After diagonal rescaling",
    )
    ax.set_xlabel("Eigenvalue index (smallest to largest)")
    ax.set_ylabel("Eigenvalue")
    ax.set_title(f"D1: Eigenvalue spectrum at stiffness ratio r = {ratio:,.0f}")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    # Fit labels, save the image, and release its memory.
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_condition_numbers(records: list[dict[str, float | int | None]], path: Path) -> None:
    """Create the D2 condition-number plot across the stiffness-ratio sweep."""

    # Extract plotting arrays from the row-oriented diagnostic records.
    ratios = np.array([record["stiffness_ratio"] for record in records], dtype=float)
    original = np.array([record["condition_number"] for record in records], dtype=float)
    scaled = np.array([record["scaled_condition_number"] for record in records], dtype=float)
    # Both axes use logarithmic scales because both quantities span decades.
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.loglog(ratios, original, "o-", linewidth=2, color="#176B87", label="Original K")
    ax.loglog(ratios, scaled, "s-", linewidth=2, color="#D1495B", label="Diagonally rescaled K")
    ax.set_xlabel(r"Stiffness ratio $r=(EA/L)_{stiff}/(EA/L)_{soft}$")
    ax.set_ylabel(r"Condition number $\kappa$")
    ax.set_title("D2: Ill-conditioning grows with the structural stiffness ratio")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    # Fit labels, save the image, and release its memory.
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_convergence(model: TrussModel, ratio: float, path: Path) -> None:
    """Create the D3-D4 before-and-after convergence comparison."""

    # Build the original reduced system used by baseline GD and ordinary CG.
    stiffness, load, _ = reduce_system(model, assemble_stiffness(model, ratio))
    # Find the full gradient-descent iteration range needed for the plot.
    _, _, gd_iterations = gradient_descent_diagnostics(stiffness, load, np.array([0]))
    # A missing count means that the requested convergence curve is unavailable.
    if gd_iterations is None:
        raise RuntimeError("Gradient descent did not reach the plotting tolerance.")
    # Sample every early step and logarithmically spaced later steps.
    gd_samples = np.unique(
        np.concatenate(
            (
                np.arange(0, 25, dtype=int),
                np.geomspace(25, gd_iterations, 350).astype(int),
            )
        )
    )
    # Evaluate the exact gradient-descent curve at those sample locations.
    _, gd_gaps, _ = gradient_descent_diagnostics(stiffness, load, gd_samples)
    # Run traditional CG on the original system and record its energy error.
    _, cg_gaps, _ = conjugate_gradient(stiffness, load)

    # Values below this floor are visually identical for the report purpose.
    plot_floor = 1.0e-12
    # A second panel makes the short CG history visible on a linear x-axis.
    early_limit = len(cg_gaps) - 1
    early_iterations = np.arange(early_limit + 1, dtype=int)
    _, gd_early_gaps, _ = gradient_descent_diagnostics(
        stiffness, load, early_iterations
    )
    # Both panels use a linear iteration axis and a logarithmic error axis.
    fig, (full_ax, early_ax) = plt.subplots(
        1, 2, figsize=(11, 4.8), sharey=True, gridspec_kw={"width_ratios": [1.35, 1.0]}
    )
    full_ax.semilogy(
        gd_samples,
        np.maximum(gd_gaps, plot_floor),
        color="#176B87",
        linewidth=2.2,
        label="Gradient descent",
    )
    full_ax.semilogy(
        np.arange(len(cg_gaps)),
        np.maximum(cg_gaps, plot_floor),
        "o-",
        color="#E09F3E",
        label="Conjugate gradient",
    )
    early_ax.semilogy(
        early_iterations,
        np.maximum(gd_early_gaps, plot_floor),
        color="#176B87",
        linewidth=2.2,
    )
    early_ax.semilogy(
        np.arange(len(cg_gaps)),
        np.maximum(cg_gaps, plot_floor),
        "o-",
        color="#E09F3E",
    )
    # The dashed line marks the common energy-error target used in D4.
    for axis in (full_ax, early_ax):
        axis.axhline(
            1.0e-8,
            color="#555555",
            linestyle="--",
            linewidth=1,
            label=r"$10^{-8}$ energy tolerance" if axis is full_ax else None,
        )
        axis.set_xlabel("Iteration number")
        axis.set_ylim(plot_floor, 2.0)
        axis.grid(True, which="both", alpha=0.25)
    full_ax.set_ylabel("Relative potential-energy error")
    full_ax.set_title("Full iteration range")
    full_ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
    early_ax.set_title("First CG iterations")
    early_ax.set_xlim(0, early_limit)
    full_ax.legend(frameon=False, fontsize=9)
    fig.suptitle(f"D3-D4: Optimizer convergence at r = {ratio:,.0f}")
    # Fit labels, save the image, and release its memory.
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_effective_rates(records: list[dict[str, float | int | None]], path: Path) -> None:
    """Plot the average fraction of energy error removed by each iteration."""
    # Extract the stiffness ratio and observed retention factor for each method.
    ratios = np.array([record["stiffness_ratio"] for record in records], dtype=float)
    gd_rates = np.array([record["gd_effective_rate"] for record in records], dtype=float)
    cg_rates = np.array([record["cg_effective_rate"] for record in records], dtype=float)
    # Plot 1-rho so larger values mean more error removed in each iteration.
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.loglog(
        ratios,
        1.0 - gd_rates,
        "o-",
        linewidth=2,
        color="#176B87",
        label="Gradient descent",
    )
    ax.loglog(
        ratios,
        1.0 - cg_rates,
        "s-",
        linewidth=2,
        color="#E09F3E",
        label="Conjugate gradient",
    )
    ax.set_xlabel(r"Stiffness ratio $r=(EA/L)_{stiff}/(EA/L)_{soft}$")
    ax.set_ylabel(r"Average energy error removed per iteration, $1-\rho_{eff}$")
    ax.set_title("D4: Effective convergence improvement")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    # Fit labels, save the image, and release its memory.
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def write_results(records: list[dict[str, float | int | None]], verification: dict[str, float | bool]) -> None:
    """Write the numerical evidence used by the report."""

    # Create the output directory if this is the first program run.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Use the first record's keys as column names for the diagnostic table.
    with (OUTPUT_DIR / "diagnostics.csv").open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    # Indented JSON keeps the verification results readable without software.
    with (OUTPUT_DIR / "verification.json").open("w", encoding="utf-8") as output_file:
        json.dump(verification, output_file, indent=2)


def write_displacement_results(
    model: TrussModel,
    stiffness_ratio: float,
    full_displacement: np.ndarray,
    reduced_displacement: np.ndarray,
    free_dofs: np.ndarray,
    deformation_scale: float,
) -> None:
    """Store u in vector and node-table forms for reporting and ANSYS checks."""

    # Reshape full u so each CSV row contains one node's two displacement values.
    nodal_displacement = full_displacement.reshape((-1, 2))
    # Save a readable node table that can be compared directly with ANSYS PRNSOL.
    with (OUTPUT_DIR / "displacements_r10000.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output_file:
        writer = csv.writer(output_file)
        writer.writerow(
            [
                "node",
                "x_config",
                "y_config",
                "x_ansys_mm",
                "y_ansys_mm",
                "u_x_mm",
                "u_y_mm",
                "magnitude_mm",
                "x_deformed_mm",
                "y_deformed_mm",
            ]
        )
        for node, (coordinates, displacement) in enumerate(
            zip(model.coordinates, nodal_displacement)
        ):
            magnitude = float(np.linalg.norm(displacement))
            # ANSYS uses a 1000 mm scale for each configuration coordinate unit.
            x_ansys = ANSYS_COORDINATE_SCALE_MM * float(coordinates[0])
            y_ansys = ANSYS_COORDINATE_SCALE_MM * float(coordinates[1])
            writer.writerow(
                [
                    node,
                    float(coordinates[0]),
                    float(coordinates[1]),
                    x_ansys,
                    y_ansys,
                    float(displacement[0]),
                    float(displacement[1]),
                    magnitude,
                    x_ansys + float(displacement[0]),
                    y_ansys + float(displacement[1]),
                ]
            )
    # JSON preserves the exact vector order used by the finite element equations.
    stiffness_full = assemble_stiffness(model, stiffness_ratio)
    # K_full*u-f contains support reactions at constrained coordinates.
    reaction_vector = stiffness_full @ full_displacement - model.load
    displacement_data = {
        "stiffness_ratio": stiffness_ratio,
        "vector_order": "[u_0x, u_0y, u_1x, u_1y, ...]",
        "free_dofs": free_dofs.tolist(),
        "reduced_u": reduced_displacement.tolist(),
        "full_u": full_displacement.tolist(),
        "full_load_vector": model.load.tolist(),
        "full_reaction_vector": reaction_vector.tolist(),
        "maximum_displacement": float(np.max(np.linalg.norm(nodal_displacement, axis=1))),
        "ansys_coordinate_scale_mm_per_config_unit": ANSYS_COORDINATE_SCALE_MM,
        "visual_deformation_scale": deformation_scale,
    }
    with (OUTPUT_DIR / "u_r10000.json").open("w", encoding="utf-8") as output_file:
        json.dump(displacement_data, output_file, indent=2)


def write_ansys_input(model: TrussModel, stiffness_ratio: float, path: Path) -> None:
    """Write an ANSYS MAPDL model that exactly matches the normalized Python truss."""

    # Use mm, N, and MPa with a typical steel Young's modulus.
    youngs_modulus = ANSYS_YOUNGS_MODULUS_MPA
    # Use the same coordinate conversion stored with the displacement output.
    coordinate_scale = ANSYS_COORDINATE_SCALE_MM
    lines = [
        "! ANSYS MAPDL verification model generated by project2_truss.py",
        "! Consistent units: mm, N, MPa. Python node n is MAPDL node n+1.",
        "/CLEAR",
        "/PREP7",
        "ET,1,LINK180",
        f"MP,EX,1,{youngs_modulus:.16g}",
        "MP,PRXY,1,0.3",
        "TYPE,1",
        "MAT,1",
    ]
    # Create the same nodes, using one-based identifiers required by MAPDL.
    for node, (x_coordinate, y_coordinate) in enumerate(model.coordinates, start=1):
        x_ansys = coordinate_scale * x_coordinate
        y_ansys = coordinate_scale * y_coordinate
        lines.append(f"N,{node},{x_ansys:.16g},{y_ansys:.16g},0")
    # LINK180 is a 3D element, so constrain out-of-plane motion at every node.
    for node in range(1, len(model.coordinates) + 1):
        lines.append(f"D,{node},UZ,0")
    # Give every member a section area that reproduces its configured axial k.
    for member, (node_i, node_j, group) in enumerate(model.members, start=1):
        length = coordinate_scale * float(
            np.linalg.norm(model.coordinates[node_j] - model.coordinates[node_i])
        )
        member_stiffness = stiffness_ratio if group == "stiff" else 1.0
        area = member_stiffness * length / youngs_modulus
        lines.extend(
            [
                f"SECTYPE,{member},LINK,,MEMBER_{member}",
                f"SECDATA,{area:.16g}",
                f"SECNUM,{member}",
                f"E,{node_i + 1},{node_j + 1}",
            ]
        )
    # Convert the Python support DOFs into MAPDL UX and UY constraints.
    for fixed_dof in model.fixed_dofs:
        node = int(fixed_dof // 2) + 1
        label = "UX" if fixed_dof % 2 == 0 else "UY"
        lines.append(f"D,{node},{label},0")
    # Apply every nonzero force component from the global Python load vector.
    for node, (force_x, force_y) in enumerate(model.load.reshape((-1, 2)), start=1):
        if force_x != 0.0:
            lines.append(f"F,{node},FX,{force_x:.16g}")
        if force_y != 0.0:
            lines.append(f"F,{node},FY,{force_y:.16g}")
    # Solve the linear static problem and print nodal displacement and reactions.
    lines.extend(
        [
            "ALLSEL,ALL",
            "FINISH",
            "/SOLU",
            "ANTYPE,STATIC",
            "SOLVE",
            "FINISH",
            "/POST1",
            "SET,LAST",
            "ALLSEL,ALL",
            "/OUTPUT,ansys_nodal_displacements,txt",
            "PRNSOL,U,COMP",
            "/OUTPUT",
            "/OUTPUT,ansys_reactions,txt",
            "PRRSOL",
            "/OUTPUT",
            "PLDISP,2",
            "FINISH",
        ]
    )
    # Write an ASCII input deck that MAPDL can run without manual model entry.
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> None:
    """Run the complete reproducible analysis and generate every report output."""

    # Create the figure directory if this is the first program run.
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    # Build the model from the four readable lists in truss_config.py.
    model = create_truss_model(NODES, MEMBERS, SUPPORTS, LOADS)
    # Sweep five ratios that cover four orders of magnitude.
    ratios = np.array([1, 10, 100, 1000, 10000], dtype=float)
    # Run independent numerical checks before creating report evidence.
    verification = verify_model(model)
    # Compute all D1-D4 metrics for every ratio.
    records = analyze_ratios(model, ratios)
    # Store the equilibrium displacement for the main r=10,000 report case.
    output_ratio = 10000.0
    full_u, reduced_u, free_dofs = solve_displacement(model, output_ratio)
    # Save exact numerical values before producing rounded visual summaries.
    write_results(records, verification)
    # Generate the model diagram and all required diagnostic figures.
    plot_structure(model, FIGURE_DIR / "warren_spar.png")
    plot_eigenvalue_spectrum(model, ratio=10000.0, path=FIGURE_DIR / "eigenvalue_spectrum.png")
    plot_condition_numbers(records, FIGURE_DIR / "condition_number_vs_ratio.png")
    plot_convergence(model, ratio=10000.0, path=FIGURE_DIR / "optimizer_convergence.png")
    plot_effective_rates(records, FIGURE_DIR / "effective_rate_vs_ratio.png")
    # Draw the physical displacement with an automatic visual scale factor.
    deformation_scale = plot_deformed_structure(
        model, full_u, output_ratio, FIGURE_DIR / "deformed_truss_r10000.png"
    )
    # Save u after plotting so its metadata includes the displayed scale factor.
    write_displacement_results(
        model, output_ratio, full_u, reduced_u, free_dofs, deformation_scale
    )
    # Export an independent ANSYS model with matching stiffnesses and loads.
    write_ansys_input(model, output_ratio, OUTPUT_DIR / "ansys_model_r10000.inp")

    # Print the same results to the terminal for immediate inspection.
    print("Verification")
    print(json.dumps(verification, indent=2))
    print("\nDiagnostics")
    for record in records:
        print(record)


# Run the analysis only when this file is executed, not when tests import it.
if __name__ == "__main__":
    main()

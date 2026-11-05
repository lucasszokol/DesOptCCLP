from pathlib import Path

import numpy as np

from heatsink.config import load_config
from heatsink.model import HeatSinkModel
from heatsink.optimize import OptimizationProblem


ROOT = Path(__file__).resolve().parents[2]


def test_optimizer_interface_shapes_and_gradients() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    model = HeatSinkModel(config)
    full = model.initial_design()
    fixed = OptimizationProblem(model, fixed_topology=True, nonlinear=True, penalty=3.0)
    assert fixed.objective_gradient(full[:20]).shape == (20,)
    assert fixed.margins(full[:20]).shape == (2,)
    assert fixed.margins_jacobian(full[:20]).shape == (2, 20)
    topology = OptimizationProblem(model, fixed_topology=False, nonlinear=True, penalty=3.0)
    assert topology.objective_gradient(full).shape == (40,)
    np.testing.assert_allclose(topology.full_design(full), full)

from Project4.heatsink.config import load_config
from Project4.heatsink.model import HeatSinkModel
from Project4.heatsink.uncertainty import (
    CENTRAL_DIFFERENCE_STEP_SWEEP,
    uncertainty_gradient_checks,
    uncertainty_model,
)


def test_uncertainty_scenarios_preserve_limits_and_span_loads():
    model = HeatSinkModel(load_config("Project4/config.yaml"))
    scenarios = uncertainty_model(model).config.load_cases
    assert len(scenarios) == 2 * len(model.config.load_cases)
    for case, low, high in zip(model.config.load_cases, scenarios[::2], scenarios[1::2]):
        assert low.power_w < case.power_w < high.power_w
        assert low.ambient_k < case.ambient_k < high.ambient_k
        assert low.chip_limit_k == high.chip_limit_k == case.chip_limit_k


def test_uncertainty_gradient_step_sweep_avoids_single_step_cancellation():
    model = HeatSinkModel(load_config("Project4/config.yaml"))
    _, checks = uncertainty_gradient_checks(model)
    tolerance = model.config.raw["verification"]["gradient_relative_tolerance"]

    assert len(checks) == 2 * len(model.config.load_cases) * 2
    for check in checks:
        samples = check["step_sweep"]
        assert tuple(sample["step"] for sample in samples) == CENTRAL_DIFFERENCE_STEP_SWEEP
        selected = min(samples, key=lambda sample: sample["relative_error"])
        assert check["step"] == selected["step"]
        assert check["central_difference"] == selected["central_difference"]
        assert check["relative_error"] == selected["relative_error"]
        assert check["relative_error"] <= tolerance

    # This is the platform-sensitive comparison that failed on macOS when
    # 1e-6 was the only sample.  The retained sweep exposes that cancellation
    # while a larger, predeclared step recovers agreement without relaxing the
    # acceptance tolerance.
    overload_density = next(
        check
        for check in checks
        if check["scenario"] == "overload_high"
        and check["variable_family"] == "density"
    )
    smallest_step = overload_density["step_sweep"][-1]
    assert smallest_step["step"] == 1.0e-6
    assert overload_density["relative_error"] < smallest_step["relative_error"]

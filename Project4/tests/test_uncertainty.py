from Project4.heatsink.config import load_config
from Project4.heatsink.model import HeatSinkModel
from Project4.heatsink.uncertainty import uncertainty_model


def test_uncertainty_scenarios_preserve_limits_and_span_loads():
    model = HeatSinkModel(load_config("Project4/config.yaml"))
    scenarios = uncertainty_model(model).config.load_cases
    assert len(scenarios) == 2 * len(model.config.load_cases)
    for case, low, high in zip(model.config.load_cases, scenarios[::2], scenarios[1::2]):
        assert low.power_w < case.power_w < high.power_w
        assert low.ambient_k < case.ambient_k < high.ambient_k
        assert low.chip_limit_k == high.chip_limit_k == case.chip_limit_k

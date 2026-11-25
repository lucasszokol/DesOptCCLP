import copy
import json
from pathlib import Path

import pytest

from heatsink.compare_reproduction import compare_results


ROOT = Path(__file__).resolve().parents[2]


def test_reproduction_comparison_detects_stale_physical_results():
    result = json.loads((ROOT / "Project4/site/assets/results.json").read_text(encoding="utf-8"))
    compare_results(result, copy.deepcopy(result))
    changed = copy.deepcopy(result)
    changed["designs"]["optimized"]["load_cases"][0]["ks_temperature_k"] += 1.0
    with pytest.raises(ValueError, match="temperature"):
        compare_results(result, changed)
    changed = copy.deepcopy(result)
    changed["designs"]["optimized"]["heights_m"][0] += 0.01
    with pytest.raises(ValueError, match="heights"):
        compare_results(result, changed)
    changed = copy.deepcopy(result)
    changed["model_configuration"]["physics"]["linear_h_w_m2k"] += 1
    with pytest.raises(ValueError, match="configuration"):
        compare_results(result, changed)

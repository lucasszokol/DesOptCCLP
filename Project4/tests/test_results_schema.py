import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]


def test_generated_results_match_schema() -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    schema = json.loads((assets / "results.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(results, schema)


def test_snapshot_field_dimensions_and_constraint_flags() -> None:
    results = json.loads((ROOT / "Project4/site/assets/results.json").read_text(encoding="utf-8"))
    geometry = results["geometry"]
    nx, nz = geometry["base_elements_x"], geometry["base_elements_z"]
    assert nx > 0 and nz > 0
    for design in (d for d in results["designs"].values() if d is not None):
        assert len(design["base_temperature_k"]) == (nx + 1) * (nz + 1)
        count = len(geometry["fin_x_m"])
        assert len(design["heights_m"]) == len(design["densities"]) == len(design["raw_densities"]) == len(design["fin_temperature_k"]) == count
        assert all(len(profile) >= 2 for profile in design["fin_temperature_k"])
        for case in design["load_cases"]:
            assert case["passed"] == (case["scaled_constraint"] <= 0)
            assert abs(case["scaled_constraint"] - (case["ks_temperature_k"] / case["limit_k"] - 1)) < 1e-10


def test_preliminary_snapshot_does_not_claim_completed_optimization() -> None:
    results = json.loads((ROOT / "Project4/site/assets/results.json").read_text(encoding="utf-8"))
    if results["designs"]["optimized"] is None:
        assert results["status"] != "final"

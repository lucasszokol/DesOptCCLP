import json
from pathlib import Path

import jsonschema
import pytest

from heatsink.serialize import validate_final_payload


ROOT = Path(__file__).resolve().parents[2]


def test_generated_results_match_schema() -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    schema = json.loads((assets / "results.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(results, schema)


def test_final_evidence_rejects_missing_and_infeasible_results() -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    if results["status"] != "final":
        pytest.skip("final campaign has not yet generated evidence")
    schema = assets / "results.schema.json"
    validate_final_payload(results, schema, 1e-4, 1e-5)
    results["designs"]["optimized"]["load_cases"][0]["scaled_constraint"] = 0.1
    with pytest.raises(ValueError, match="infeasible"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["designs"]["optimized"]["load_cases"][0]["scaled_constraint"] = 0.0
    results["kkt"]["constraint_violation"] = float("nan")
    with pytest.raises(ValueError, match="KKT"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["kkt"]["constraint_violation"] = 0.0
    results["kkt"]["bound_complementarity"] = 0.1
    with pytest.raises(ValueError, match="KKT"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["designs"]["optimized"] = None
    with pytest.raises(jsonschema.ValidationError):
        validate_final_payload(results, schema, 1e-4, 1e-5)

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


def test_reported_kkt_matches_campaign_evidence() -> None:
    results = json.loads((ROOT / "Project4/site/assets/results.json").read_text(encoding="utf-8"))
    campaign = json.loads((ROOT / "Project4/results/optimization/campaign.json").read_text(encoding="utf-8"))
    assert results["kkt"]["bound_complementarity"] == pytest.approx(
        campaign["kkt"]["bound_complementarity_inf_norm"], rel=1e-10, abs=1e-15
    )
    assert results["kkt"]["physical_stationarity_inf_norm"] == pytest.approx(
        campaign["kkt"]["stationarity_inf_norm_physical"], rel=1e-10, abs=1e-15
    )


def test_reported_topology_matches_campaign_evidence() -> None:
    results = json.loads((ROOT / "Project4/site/assets/results.json").read_text(encoding="utf-8"))
    campaign = json.loads((ROOT / "Project4/results/optimization/campaign.json").read_text(encoding="utf-8"))
    summary = results["topology_summary"]
    evidence = campaign["topology"]

    assert summary["candidate_fins"] == evidence["candidate_fins"]
    assert summary["active_fins_after_threshold"] == evidence["active_fins_after_threshold"]
    assert summary["topology_bonus_demonstrated"] == evidence["topology_bonus_demonstrated"]
    assert not summary["discrete_removed_fin_feasibility_demonstrated"]
    assert summary["binary_density"] == pytest.approx(evidence["binary_density"])
    assert summary["threshold_filtered_density"] == pytest.approx(
        evidence["threshold_filtered_density"]
    )

    runs = {run["name"]: run for run in campaign["runs"]}
    for reported in results["topology_starts"]:
        run = runs[reported["name"]]
        raw = max(case["scaled_constraint"] for case in run["load_cases"])
        buffered = max(-case["constraint_margin"] for case in run["load_cases"])
        assert reported["max_raw_scaled_constraint"] == pytest.approx(raw)
        assert reported["max_buffered_scaled_constraint"] == pytest.approx(buffered)


def test_final_evidence_rejects_missing_and_infeasible_results() -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    if results["status"] != "final":
        pytest.skip("final campaign has not yet generated evidence")
    schema = assets / "results.schema.json"
    validate_final_payload(results, schema, 1e-4, 1e-5)
    results["nonlinear_fin_check"]["status"] = "failed"
    with pytest.raises(ValueError, match="Nonlinear fin cross-check"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["nonlinear_fin_check"]["status"] = "passed"
    results["design_mesh_validation"]["status"] = "failed"
    with pytest.raises(ValueError, match="Design mesh verification"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["design_mesh_validation"]["status"] = "passed"
    case = results["designs"]["optimized"]["load_cases"][0]
    original_balance = case["energy_imbalance_w"]
    case["energy_imbalance_w"] = case["power_w"] * 1e-3
    with pytest.raises(ValueError, match="Energy balance"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    case["energy_imbalance_w"] = original_balance
    original_peak = case["chip_peak_temperature_k"]
    case["chip_peak_temperature_k"] = case["ks_temperature_k"] + 1
    with pytest.raises(ValueError, match="chip peak"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    case["chip_peak_temperature_k"] = original_peak
    original_constraint = results["designs"]["optimized"]["load_cases"][0]["scaled_constraint"]
    results["designs"]["optimized"]["load_cases"][0]["scaled_constraint"] = 0.1
    with pytest.raises(ValueError, match="infeasible"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["designs"]["optimized"]["load_cases"][0]["scaled_constraint"] = original_constraint
    results["kkt"]["constraint_violation"] = float("nan")
    with pytest.raises(ValueError, match="KKT"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["kkt"]["constraint_violation"] = 0.0
    original_stationarity = results["kkt"]["physical_stationarity_inf_norm"]
    results["kkt"]["physical_stationarity_inf_norm"] = 0.1
    with pytest.raises(ValueError, match="KKT"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["kkt"]["physical_stationarity_inf_norm"] = original_stationarity
    results["kkt"]["bound_complementarity"] = 0.1
    with pytest.raises(ValueError, match="KKT"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["kkt"]["bound_complementarity"] = 0.0
    selected = results["uncertainty"]["gradient_checks"][0]
    selected["step"] *= 2
    with pytest.raises(ValueError, match="gradient selection"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    selected["step"] /= 2
    results["topology_summary"]["active_fins_after_threshold"] -= 1
    with pytest.raises(ValueError, match="Topology summary"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["topology_summary"]["active_fins_after_threshold"] += 1
    results["uncertainty"]["baseline_design"]["load_cases"][0]["name"] = "wrong_scenario"
    with pytest.raises(ValueError, match="Load-case coverage"):
        validate_final_payload(results, schema, 1e-4, 1e-5)
    results["designs"]["optimized"] = None
    with pytest.raises(jsonschema.ValidationError):
        validate_final_payload(results, schema, 1e-4, 1e-5)


@pytest.mark.parametrize("defect", ["missing_case", "wrong_power", "wrong_constraint", "wrong_flag", "failed_verification"])
def test_final_evidence_rejects_inconsistent_loads_and_verification(defect) -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    if results["status"] != "final":
        pytest.skip("final campaign has not yet generated evidence")
    cases = results["designs"]["initial"]["load_cases"]
    if defect == "missing_case":
        cases.pop()
    elif defect == "wrong_power":
        cases[0]["power_w"] += 1
    elif defect == "wrong_constraint":
        cases[0]["scaled_constraint"] += 0.01
    elif defect == "wrong_flag":
        cases[0]["passed"] = not cases[0]["passed"]
    else:
        results["verification"]["groups"][0]["checks"][0]["pass"] = False
    with pytest.raises((ValueError, jsonschema.ValidationError)):
        validate_final_payload(results, assets / "results.schema.json", 1e-4, 1e-5)

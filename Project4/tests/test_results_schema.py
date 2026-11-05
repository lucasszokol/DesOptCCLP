import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[2]


def test_generated_results_match_schema() -> None:
    assets = ROOT / "Project4" / "site" / "assets"
    results = json.loads((assets / "results.json").read_text(encoding="utf-8"))
    schema = json.loads((assets / "results.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(results, schema)

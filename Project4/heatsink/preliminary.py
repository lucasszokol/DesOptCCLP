"""Generate a clearly labeled pre-gate JSON file without graded truth."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .model import HeatSinkModel
from .serialize import preliminary_payload, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="Project4/config.yaml")
    arguments = parser.parse_args()
    config = load_config(arguments.config)
    model = HeatSinkModel(config)
    destination = Path(config.raw["outputs"]["results_json"])
    write_json(preliminary_payload(model), destination)
    print(f"Wrote preliminary, human-gated data to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

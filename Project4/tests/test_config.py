from pathlib import Path

from heatsink.config import load_config


ROOT = Path(__file__).resolve().parents[2]


def test_authoritative_config_loads() -> None:
    config = load_config(ROOT / "Project4" / "config.yaml")
    assert config.geometry.candidate_fins == 20
    assert len(config.load_cases) == 2
    assert config.material.conductivity_w_mk == 167.0

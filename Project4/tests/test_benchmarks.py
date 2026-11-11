from pathlib import Path

from heatsink.benchmark_verification import benchmark_verification, load_truth, main
from heatsink.config import load_config
from heatsink.model import HeatSinkModel


ROOT = Path(__file__).resolve().parents[2]


def test_complete_v1_v6_benchmark_ladder() -> None:
    truth = load_truth(ROOT / "Project4" / "tests" / "benchmark_truth.yaml")
    model = HeatSinkModel(load_config(ROOT / "Project4" / "config.yaml"))
    evidence = benchmark_verification(model, truth)
    failures = [
        f"{group['id']} {check['quantity']}: computed={check['computed']:.10g}, submitted={check['exact']:.10g}"
        for group in evidence["groups"] for check in group["checks"] if not check["pass"]
    ]
    assert not failures, "benchmark failures:\n" + "\n".join(failures)


def test_standalone_verification_command_regenerates_evidence(tmp_path: Path) -> None:
    exit_code = main(
        [
            "--config", str(ROOT / "Project4" / "config.yaml"),
            "--truth", str(ROOT / "Project4" / "tests" / "benchmark_truth.yaml"),
            "--output", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert (tmp_path / "verification.json").is_file()
    assert (tmp_path / "verification.md").is_file()

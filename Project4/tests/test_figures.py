from pathlib import Path

from heatsink.figures import generate_figures


ROOT = Path(__file__).resolve().parents[2]


def test_figures_are_regenerated_from_canonical_results(tmp_path):
    outputs = generate_figures(ROOT / "Project4/site/assets/results.json", tmp_path)
    assert {path.name for path in outputs} == {
        "mass-comparison.png", "taylor-checks.png", "uncertainty-comparison.png", "mesh-convergence.png", "design-mesh-convergence.png"
    }
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in outputs)

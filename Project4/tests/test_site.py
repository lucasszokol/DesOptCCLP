from pathlib import Path

from heatsink.site import build_site


ROOT = Path(__file__).resolve().parents[2]


def test_static_site_build_contains_report_and_assets() -> None:
    destination = build_site(ROOT / "Project4" / "site")
    html = (destination / "index.html").read_text(encoding="utf-8")
    assert "PDE-Constrained Heat-Sink Optimization" in html
    assert "__REPORT_CONTENT__" not in html
    assert (destination / "assets" / "results.json").exists()
    assert (destination / "assets" / "viewer.js").exists()

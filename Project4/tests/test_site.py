from pathlib import Path
import re

from heatsink.site import build_site


ROOT = Path(__file__).resolve().parents[2]


def test_static_site_build_contains_report_and_assets() -> None:
    destination = build_site(ROOT / "Project4" / "site")
    html = (destination / "index.html").read_text(encoding="utf-8")
    assert "PDE-Constrained Heat-Sink Optimization" in html
    assert "__REPORT_CONTENT__" not in html
    assert (destination / "assets" / "results.json").exists()
    assert (destination / "assets" / "viewer.js").exists()
    # These results must remain visible in the HTML without the viewer module.
    for panel, evidence in [
        ("verification-summary", "V1: T(1/4L)"),
        ("sensitivity-summary", "Taylor slope"),
        ("kkt-summary", "stationarity"),
        ("comparison-summary", "Mean fin heights"),
        ("uncertainty-summary", "Scenario optimum KS"),
    ]:
        match = re.search(rf'<div id="{panel}"[^>]*>(.*?)</div>', html, re.DOTALL)
        assert match is not None and evidence in match.group(1)
    assert "Verification evidence awaits" not in html
    assert "Uncertainty study awaits" not in html

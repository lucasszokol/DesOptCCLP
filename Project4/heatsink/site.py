"""Deterministically build the Markdown report into a static Pages artifact."""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

import markdown


def _table(headers: list[str], rows: list[list[object]]) -> str:
    def cells(tag: str, values: list[object]) -> str:
        return "<tr>" + "".join(f"<{tag}>{html.escape(str(value))}</{tag}>" for value in values) + "</tr>"

    return "<table><thead>" + cells("th", headers) + "</thead><tbody>" + "".join(cells("td", row) for row in rows) + "</tbody></table>"


def _static_evidence(report: str, data: dict) -> str:
    """Render readable evidence from the same JSON used by the interactive viewer."""
    if data.get("status") != "final":
        return report
    verification = data["verification"]
    checks = [[f"{group['id']}: {check['quantity']}", f"{check['computed']:.7g}",
               f"{check['exact']:.7g}", f"{check['absolute_error']:.2e}",
               "—" if check["exact"] == 0 else f"{check['relative_error']:.2e}",
               f"{check['tolerance']:.2e}", "PASS" if check["pass"] else "FAIL"]
              for group in verification["groups"] for check in group["checks"]]
    v = (f"<p>Status: {html.escape(verification['status'])}; {verification['passed_checks']}/{verification['total_checks']} checks passed. Relative error is omitted when the reference is zero.</p>"
         + _table(["Check", "Computed", "Reference", "Absolute error", "Relative error", "Tolerance", "Result"], checks)
         + f"<p>{html.escape(verification['student_attestation'])}</p>")
    gradients = [[c["load_case"], c["variable_family"], f"{c['taylor_slope']:.3f}",
                  f"{c['minimum_relative_directional_error']:.2e}", "PASS" if c["pass"] else "FAIL"]
                 for c in data["gradient_checks"]]
    cost = data["sensitivity_cost"]
    sensitivity = (_table(["Case", "Variables", "Taylor slope", "Best relative error", "Check"], gradients)
        + f"<p>For {cost['design_variables']} variables, one state plus adjoint took {cost['adjoint_seconds']:.3f} s; {cost['central_difference_state_solves']} central-difference state solves took {cost['finite_difference_seconds']:.3f} s ({cost['speedup']:.1f}× on this machine). Full-gradient relative error: {cost['relative_gradient_error']:.2e}.</p>")
    k = data["kkt"]
    mu = k["multipliers"][0]
    marginal = -mu[1] * data["designs"]["initial"]["mass_kg"] / data["designs"]["optimized"]["load_cases"][1]["limit_k"]
    kkt = (f"<p>KKT convergence: {html.escape(k['message'])}; stationarity {k['optimality']:.3e}, constraint violation {k['constraint_violation']:.3e}, thermal complementarity {k['constraint_complementarity']:.3e}, bound complementarity {k['bound_complementarity']:.3e}. Scaled signed constraint multipliers (nominal, overload): {mu[0]:.5g}, {mu[1]:.5g}. Negative signs follow SciPy's lower-bound convention for the positive margin; the large overload magnitude identifies the active thermal requirement. Locally, a 1 K relaxation of the overload limit is estimated to reduce mass by {marginal:.3g} kg, holding the active set and model fixed.</p>")
    linear, nonlinear = data["designs"]["linear_fixed"], data["designs"]["nonlinear_fixed"]
    difference = 100 * (nonlinear["mass_kg"] / linear["mass_kg"] - 1)
    mean = lambda values: sum(values) / len(values) * 1000
    change = max(abs(a - b) for a, b in zip(linear["heights_m"], nonlinear["heights_m"])) * 1000
    comparison = (f"<p>Linear fixed-topology mass: {linear['mass_kg']:.5f} kg; nonlinear fixed-topology mass: {nonlinear['mass_kg']:.5f} kg ({difference:+.1f}%). Mean fin heights: {mean(linear['heights_m']):.2f} mm and {mean(nonlinear['heights_m']):.2f} mm, respectively; maximum individual height change: {change:.2f} mm. The original uniform design fails the thermal requirements and is not a feasible mass-saving baseline.</p>")
    u = data["uncertainty"]
    baseline = u["baseline_design"]
    robust = u["design"]
    scenarios = []
    for case in robust["load_cases"]:
        original = next(item for item in baseline["load_cases"] if item["name"] == case["name"])
        fmt = lambda c: f"{c['ks_temperature_k']:.4f} / {c['limit_k']:.2f} {'PASS' if c['passed'] else 'FAIL'}"
        scenarios.append([case["name"], fmt(original), fmt(case)])
    uncertainty = (f"<p>Power variation ±{100*u['assumptions']['power_fraction']:.1f}%; ambient variation ±{u['assumptions']['ambient_delta_k']:.2f} K. Nominal optimum mass: {baseline['mass_kg']:.6f} kg; scenario-optimized mass: {robust['mass_kg']:.6f} kg ({100*(robust['mass_kg']/baseline['mass_kg']-1):+.2f}%).</p>"
        + _table(["Scenario", "Nominal optimum KS / limit (K)", "Scenario optimum KS / limit (K)"], scenarios)
        + f"<p>Worst directional gradient relative error: {max(c['relative_error'] for c in u['gradient_checks']):.3e}.</p>")
    replacements = {
        '<div id="verification-summary" class="data-panel">Verification data is loading from the generated results.</div>': f'<div id="verification-summary" class="data-panel">{v}</div>',
        '<div id="sensitivity-summary"></div>': f'<div id="sensitivity-summary">{sensitivity}</div>',
        '<div id="kkt-summary"></div>': f'<div id="kkt-summary">{kkt}</div>',
        '<div id="comparison-summary"></div>': f'<div id="comparison-summary">{comparison}</div>',
        '<div id="uncertainty-summary">Uncertainty results are loading from the generated data.</div>': f'<div id="uncertainty-summary">{uncertainty}</div>',
    }
    for marker, value in replacements.items():
        if marker not in report:
            raise ValueError(f"report is missing evidence marker: {marker}")
        report = report.replace(marker, value, 1)
    return report


def _strip_front_matter(source: str) -> str:
    if not source.startswith("---\n"):
        return source
    end = source.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated Markdown front matter")
    return source[end + 5 :]


def build_site(source_directory: str | Path) -> Path:
    source = Path(source_directory).resolve()
    destination = source / "_site"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    report = _strip_front_matter((source / "index.md").read_text(encoding="utf-8"))
    report = _static_evidence(report, json.loads((source / "assets" / "results.json").read_text(encoding="utf-8")))
    content = markdown.markdown(
        report,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html5",
    )
    layout = (source / "_layouts" / "default.html").read_text(encoding="utf-8")
    if "__REPORT_CONTENT__" not in layout:
        raise ValueError("layout is missing __REPORT_CONTENT__ marker")
    (destination / "index.html").write_text(
        layout.replace("__REPORT_CONTENT__", content), encoding="utf-8"
    )
    shutil.copytree(source / "assets", destination / "assets")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="Project4/site")
    arguments = parser.parse_args()
    destination = build_site(arguments.source)
    print(f"Built static report at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

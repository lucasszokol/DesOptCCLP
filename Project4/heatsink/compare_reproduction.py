"""Compare publishable engineering results before and after regeneration."""

import argparse
import json
from pathlib import Path

import numpy as np


def compare_results(committed: dict, regenerated: dict) -> None:
    """Compare physical results within numerical tolerances, excluding wall times.

    Optimizer iteration histories and wall timings can vary by machine. This
    check covers the configurations, final design geometry, masses, and load
    responses that the Pages build will publish; it is not a byte-for-byte
    comparison of every diagnostic or image.
    """
    if committed.get("status") != "final" or regenerated.get("status") != "final":
        raise ValueError("Both committed and regenerated results must be final")
    if committed["model_configuration"] != regenerated["model_configuration"]:
        raise ValueError("Committed configuration differs from regenerated configuration")

    def close(label, a, b, *, rtol=1e-4, atol=1e-8):
        try:
            equal = np.allclose(a, b, rtol=rtol, atol=atol, equal_nan=False)
        except (TypeError, ValueError):
            equal = False
        if not equal:
            raise ValueError(f"Committed and regenerated {label} differ beyond tolerance")

    def design(label, a, b):
        close(f"{label} mass", a["mass_kg"], b["mass_kg"], atol=1e-7)
        close(f"{label} heights", a["heights_m"], b["heights_m"], rtol=1e-3, atol=2e-5)
        close(f"{label} densities", a["densities"], b["densities"], atol=1e-3)
        close(f"{label} base temperatures", a["base_temperature_k"], b["base_temperature_k"], rtol=0, atol=0.02)
        close(f"{label} fin temperatures", a["fin_temperature_k"], b["fin_temperature_k"], rtol=0, atol=0.02)
        ac = {case["name"]: case for case in a["load_cases"]}
        bc = {case["name"]: case for case in b["load_cases"]}
        if len(ac) != len(a["load_cases"]) or len(bc) != len(b["load_cases"]) or ac.keys() != bc.keys():
            raise ValueError(f"Committed and regenerated {label} load cases differ")
        for name in ac:
            for field in ("power_w", "ambient_k", "limit_k", "ks_temperature_k", "chip_peak_temperature_k"):
                close(f"{label} {name} {field}", ac[name][field], bc[name][field], rtol=0, atol=0.02 if "temperature" in field else 1e-10)
            if ac[name]["passed"] != bc[name]["passed"]:
                raise ValueError(f"Committed and regenerated {label} {name} pass status differs")

    for key in ("initial", "optimized", "linear_fixed", "nonlinear_fixed"):
        design(key, committed["designs"][key], regenerated["designs"][key])
    for key in ("design", "baseline_design"):
        design(f"uncertainty {key}", committed["uncertainty"][key], regenerated["uncertainty"][key])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("committed", type=Path)
    parser.add_argument("regenerated", type=Path)
    args = parser.parse_args()
    compare_results(json.loads(args.committed.read_text(encoding="utf-8")),
                    json.loads(args.regenerated.read_text(encoding="utf-8")))
    print("Committed and regenerated engineering results agree within documented tolerances.")


if __name__ == "__main__":
    main()

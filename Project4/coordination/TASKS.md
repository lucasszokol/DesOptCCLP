# Parallel Task Ownership

Only Agent 5 updates this table after reviewing GitHub evidence.

| Lane | GitHub issue title | Branch | Exclusive write ownership | Completion evidence |
|---|---|---|---|---|
| Agent 1 — Physics verification | `[P4-A1] Independent FE benchmark verification` | `agent/physics-verification` | `Project4/heatsink/benchmark_verification.py`, `Project4/tests/test_benchmarks.py`, `Project4/results/verification/` | V1–V7 table, exact/convergence/balance/invariance/N2 checks, full tests |
| Agent 2 — Adjoint sensitivity | `[P4-A2] Adjoint and Taylor evidence` | `agent/adjoint-sensitivity` | `Project4/heatsink/verification.py`, `Project4/tests/test_sensitivity.py`, `Project4/results/sensitivity/` | Every constraint and variable family checked, Taylor slopes, timing comparison |
| Agent 3 — Optimization/topology | `[P4-A3] Optimization and topology campaign` | `agent/optimization-topology` | `Project4/heatsink/optimize.py`, `campaign.py`, `topology.py`, `Project4/tests/test_optimize.py`, `test_topology.py`, `Project4/results/optimization/` | Feasible linear/N2/fixed/topology designs, KKT evidence, binary threshold comparison |
| Agent 4 — Report/viewer | `[P4-A4] Report and interactive viewer` | `agent/report-viewer` | `Project4/site/`, `Project4/heatsink/serialize.py`, `site.py`, `Project4/tests/test_site.py`, `test_results_schema.py` | Eight viewer requirements, phone layout, report sections, schema and visual QA evidence |
| Agent 5 — Integration/audit | `[P4-A5] Integration and 110-point audit` | `agent/integration-audit` | `Project4/heatsink/run_all.py`, `gates.py`, `config.py`, `Project4/config.yaml`, requirements, README, `RUBRIC_AUDIT.md`, `.github/workflows/project4-pages.yml`, `Project4/coordination/` | Integrated clean run, 110-point evidence ledger, CI, deploy-ready artifact, no unsupported claims |

## Shared read-only contracts

All agents may read but may not independently rewrite:

- `Project4/SPECIFICATION.md`
- `Project4/approvals.yaml`
- `Project4/tests/benchmark_truth.yaml`
- `Project4/heatsink/model.py`
- `Project4/heatsink/elements.py`

If a shared contract is wrong, file an issue with evidence. Agent 5 coordinates
the smallest authorized correction after team approval.

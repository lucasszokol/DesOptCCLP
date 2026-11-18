# Agent 5 specialist review — 2026-11-17

This review uses the pull-request commits and live issue state. No specialist
branch was merged or copied into the integration branch.

## Agent 1 — PR #8, commit `2709aa0`

The pull request is open and reports 20/20 standalone benchmark checks, two
focused tests, and 20 full-suite tests. The change stays within the declared
Agent 1 paths. Before acceptance, a reviewer should confirm the standalone
entry point invokes the complete human gate rather than reading the truth file
alone. This is not yet merged evidence.

## Agent 2 — PR #14, commit `35caa92`

The pull request is open and reports 72/72 directional/Taylor sweeps, focused
and full-suite success, and corrected finite-difference timing. Its own
integration note states that baseline `run_all.py` can overwrite the expanded
sensitivity evidence with a subset. Acceptance therefore requires preserving
the expanded generator in the final one-command path and resolving provenance
for source archives without Git metadata.

## Agent 3 — issue #10

There is no remote `agent/optimization-topology` branch and no pull request.
The issue records three acceptance failures: the linear fixed-topology result
is infeasible, the topology result is all-solid, and the final KKT polish
fails. It also records that thresholded raw densities are filtered again, so a
mixed raw design is not a binary physical design. This lane blocks final
integration and both optimization-dependent bonuses.

## Agent 4 — draft PR #15, commit `cb22fdb`

The draft correctly labels its results preliminary and does not invent final
optimization data. Focused schema/site checks and the full suite are reported
as passing. It is not review-ready because final campaign data, desktop and
390 px visual inspection, WebGL interaction, field mapping, and formula
rendering remain unverified.

## Integration decision

PRs #8 and #14 can proceed to maintainer review. PR #15 must remain draft, and
Agent 3 must publish a branch and pull request before Agent 5 can perform final
integration. The integration branch must not claim 110/100 or deploy final
data until all fixed acceptance gates pass.

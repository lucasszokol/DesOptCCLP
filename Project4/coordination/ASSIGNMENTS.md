# Project 4 agent assignments

These assignments map the five repository collaborators to exclusive Project 4
lanes. GitHub issue assignment is the authoritative current status; agents must
still use the exact branches and ownership boundaries in `TASKS.md`.

| Agent lane | Teammate / GitHub account | Issue | Branch | Current state |
|---|---|---|---|---|
| Agent 1 — Physics verification | Charles Green / `crgree17-ship-it` | [#7](https://github.com/lucasszokol/DesOptCCLP/issues/7) | `agent/physics-verification` | Review PR #8 and continue only within the Agent 1 lane |
| Agent 2 — Adjoint sensitivity | Christian Miranda / `christianmiranda-ai` | [#9](https://github.com/lucasszokol/DesOptCCLP/issues/9) | `agent/adjoint-sensitivity` | Assigned; branch and PR pending |
| Agent 3 — Optimization/topology | Kellen Worthington / `kaworthi` | [#10](https://github.com/lucasszokol/DesOptCCLP/issues/10) | `agent/optimization-topology` | DEC-002 approved; resume optimization/topology campaign |
| Agent 4 — Report/viewer | Polina Kondratiuk / `pkondratkippy` | [#11](https://github.com/lucasszokol/DesOptCCLP/issues/11) | `agent/report-viewer` | Assigned; may address data-independent viewer/report gaps now |
| Agent 5 — Integration/audit | Lucas Somoshegyi-Szokol / `lucasszokol` | [#12](https://github.com/lucasszokol/DesOptCCLP/issues/12) | `agent/integration-audit` | PR #13 open; DEC-002 cleared, awaiting Agent 3 campaign integration |

## Coordination rule

Do not push commits to another lane's branch. Report an out-of-lane defect in
that lane's issue and wait for its PR. Agent 5 reviews accepted PRs and reruns
the one-command reproduction after the maintainer merges them to `main`.

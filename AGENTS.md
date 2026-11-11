# Repository instructions for coding agents

These instructions apply to every agent working in this repository.

## Project orientation

The active course deliverable is `Project4/`, a PDE-constrained heat-sink
optimization targeting the complete 100-point rubric plus the fully nonlinear
and topology bonuses. Before changing files, read:

1. `Project4/SPECIFICATION.md`
2. `Project4/RUBRIC_AUDIT.md`
3. `Project4/coordination/README.md`
4. `Project4/coordination/TASKS.md`
5. The task file and Goal prompt for your assigned lane

Treat the checked-out repository and merged Git history as authoritative.
Conversation memory, another agent's unmerged branch, and status narration are
not evidence.

## Human verification gate

Do not calculate, invent, infer, or replace the student benchmark answers.
Graded optimization may begin only when both files exist and validate:

- `Project4/approvals.yaml` with `specification_approved: true`
- `Project4/tests/benchmark_truth.yaml` with `status: student_verified` and a
  non-empty student attestation

If either file is absent or incomplete, stop and report the exact missing human
input. Never weaken, bypass, mock, or auto-fill the gate.

## Concurrent Git workflow

- Never work directly on `main`.
- Pull the latest `main`, then create the exact branch named for your task lane.
- Edit only files owned by that lane. Read-only inspection outside the lane is
  allowed.
- Do not modify `Project4/coordination/TASKS.md`; Agent 5 owns integration state.
- Do not merge another agent's branch. Open a pull request and wait for review.
- Before pushing, rebase or merge the latest `origin/main`, resolve only
  conflicts inside your owned files, and rerun verification.
- Record material discoveries, commands, test evidence, unresolved risks, and
  the commit SHA in a unique file under `Project4/coordination/handoffs/`.
- Never commit credentials, tokens, browser sessions, student account data, or
  private course information.

## Verification baseline

From the repository root, use the repository-local environment when present:

```powershell
.\.venv\Scripts\python.exe -m pytest Project4\tests -q
.\.venv\Scripts\python.exe -m Project4.heatsink.site --source Project4\site
node --check Project4\site\assets\viewer.js
git diff --check
```

On Linux or CI, replace the Python executable with `python`.

Do not claim a requirement passed unless the command was actually run and its
output is recorded. A focused test does not prove the whole project passes.

## External actions

The copy-ready Goal prompt authorizes its agent to create its named branch,
commit its scoped work, push that branch, create/update its GitHub issue, and
open a pull request. It does not authorize merging to `main`, enabling Pages,
submitting Canvas, changing repository permissions, or handling credentials.

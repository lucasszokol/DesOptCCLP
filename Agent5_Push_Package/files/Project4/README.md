# Project 4 — PDE-Constrained Heat-Sink Optimization

This project develops and verifies a custom finite-element thermal model, its
discrete adjoint, and a ground-structure topology optimization for a naturally
cooled 6061-T6 aluminum heat sink. The report and viewer consume the single
canonical file `site/assets/results.json`.

## Current integration status

The human gate is complete on `main`. The baseline suite passes, but the final
graded campaign is not yet reproducible: the `trust-constr` KKT stage evaluates
an inadmissible non-positive fin height. GitHub issue
[`#10`](https://github.com/lucasszokol/DesOptCCLP/issues/10) owns that Agent 3
defect. Agent 3 has not published the required branch or pull request, and the
Agent 4 report pull request remains a draft pending final optimization data.

No final score, topology bonus, or deployable final result is claimed while
those conditions remain unresolved.

## Human gate

Every graded run first validates both human-authored records:

- `approvals.yaml` must record specification approval, the approvers, and the
  approval date.
- `tests/benchmark_truth.yaml` must have `status: student_verified` and a
  non-empty student attestation.

The program never creates or alters the student benchmark truth.

## Reproduction

From the repository root, create an isolated environment and install the
declared dependencies:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r Project4/requirements.txt
```

On Windows, replace `.venv/bin/python` with `.venv\Scripts\python.exe`.

The complete evidence and report command is:

```bash
.venv/bin/python -m Project4.heatsink.run_all --config Project4/config.yaml
```

It validates the human gate, regenerates benchmark and sensitivity evidence,
runs every optimization stage, enforces the fixed scaled-feasibility tolerance
of `1e-4`, requires a retained-and-removed-fin topology with a discrete
physical-density check, writes canonical results, and builds the static site.
It returns a nonzero status and does not write final JSON if any stage fails.

Run the shorter review checks with:

```bash
.venv/bin/python -m Project4.heatsink.run_all --check-gates
.venv/bin/python -m pytest Project4/tests -q
.venv/bin/python -m Project4.heatsink.site --source Project4/site
node --check Project4/site/assets/viewer.js
git diff --check
```

## Team

Charles Green, Christian Miranda, Lucas Somoshegyi-Szokol, and Polina
Kondratiuk.

## Remaining human-only actions

1. Review and merge accepted Agent 1–4 pull requests through the maintainer
   workflow.
2. Review the final AI-use statement.
3. Enable or approve GitHub Pages deployment and verify the live site in a
   private browser window.
4. Submit the repository and site URLs to Canvas.

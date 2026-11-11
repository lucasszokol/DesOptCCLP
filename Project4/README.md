# Project 4 — PDE-Constrained Heat-Sink Optimization

This project develops and verifies a custom finite-element thermal model, its
discrete adjoint, and a ground-structure topology optimization for a naturally
cooled 6061-T6 aluminum heat sink. The final report and interactive comparison
are generated from one canonical `site/assets/results.json` file.

## Links

- Repository: <https://github.com/lucasszokol/DesOptCCLP>
- Live report: <https://lucasszokol.github.io/DesOptCCLP/>
- Integration status: [issue #12](https://github.com/lucasszokol/DesOptCCLP/issues/12)
- Agent assignments: [`coordination/ASSIGNMENTS.md`](coordination/ASSIGNMENTS.md)

## Current status

- The specification approval and student-authored benchmark gates pass.
- V1--V6 reports 20/20 checks passing; V7 adjoint/Taylor evidence passes.
- GitHub Pages test, build, and deployment jobs pass, and the public site
  responds successfully.
- The full optimization command currently reaches the final KKT stage and then
  fails on the bound-handling defect tracked in
  [issue #10](https://github.com/lucasszokol/DesOptCCLP/issues/10).
- The live site therefore still shows preliminary data. Do not present it as a
  final optimized result yet.

## Human gates

The completed benchmark derivations remain in
[`HUMAN_BENCHMARK_WORKSHEET.md`](HUMAN_BENCHMARK_WORKSHEET.md), and their
transcription/attestation is read-only solver truth. Agents must not replace
those answers.

An additional decision is now required because the approved 50 mm height cap
cannot produce a feasible thresholded design with even one vanished fin. See
[`DEC-002-optimization-feasibility.md`](coordination/decisions/DEC-002-optimization-feasibility.md).

## Intended reproducibility command

```powershell
.\.venv\Scripts\python.exe -m Project4.heatsink.run_all --config Project4\config.yaml
```

The command will run verification, gradient checks, the three optimization
cases, report-table generation, JSON serialization, and the static-site build.
It must exit successfully before `site/assets/results.json` is treated as final.

## Team

Charles Green, Christian Miranda, Lucas Somoshegyi-Szokol, and Polina
Kondratiuk.

## Remaining human actions

- Approve or revise DEC-002.
- Confirm whether Kellen Worthington is a Project 4 author; the benchmark
  attestation and collaborator list include Kellen, while current report
  attribution does not.
- After the final campaign and site QA pass, submit both URLs on Canvas.

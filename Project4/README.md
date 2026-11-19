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
- The current public site follows `main`. An audit found mesh dependence in
  its reported KS constraint and a mismatch in the chip footprint.
- The proposed DEC-003 branch corrects those issues, adds a 0.5 K numerical
  reserve, sparse assembly, and design-level mesh verification. The team must
  review the amendment and regenerated designs before final submission.

## Human gates

The completed benchmark derivations remain in
[`HUMAN_BENCHMARK_WORKSHEET.md`](HUMAN_BENCHMARK_WORKSHEET.md), and their
transcription/attestation is read-only solver truth. Agents must not replace
those answers.

The team approved the DEC-002 feasibility amendment: a 55 mm height cap,
linear comparison coefficient of 15 W/(m² K), and design under uncertainty as
the backup bonus path. See
[`DEC-002-optimization-feasibility.md`](coordination/decisions/DEC-002-optimization-feasibility.md).
The later numerical amendment is documented in
[`DEC-003-mesh-consistency.md`](coordination/decisions/DEC-003-mesh-consistency.md).

## Intended reproducibility command

```powershell
.\.venv\Scripts\python.exe -m Project4.heatsink.run_all --config Project4\config.yaml
```

The command runs verification, gradient checks, optimization, uncertainty
scenarios, final-data validation, JSON serialization, and the static-site build.
It must exit successfully before `site/assets/results.json` is treated as final.

## Team

Charles Green, Christian Miranda, Kellen Worthington, Lucas
Somoshegyi-Szokol, and Polina Kondratiuk.

## Remaining human actions

- Review DEC-003 and the revised numerical results, then verify the deployed
  site in a private window and confirm the participation-sheet URL.
- After the final campaign and site QA pass, submit both URLs on Canvas.

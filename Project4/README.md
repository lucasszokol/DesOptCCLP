# Project 4 — PDE-Constrained Heat-Sink Optimization

This project develops and verifies a custom finite-element thermal model, its
discrete adjoint, and a ground-structure topology optimization for a naturally
cooled 6061-T6 aluminum heat sink. The final report and interactive comparison
are generated from one canonical `site/assets/results.json` file.

## Required human gate

Do **not** add expected benchmark answers to the automated tests until the team
has completed [`HUMAN_BENCHMARK_WORKSHEET.md`](HUMAN_BENCHMARK_WORKSHEET.md).
The course brief requires the students to derive the verification truth
independently of the coding agent.

The team must also approve [`SPECIFICATION.md`](SPECIFICATION.md) before the
full optimization campaign begins.

## Intended reproducibility command

```powershell
python -m Project4.heatsink.run_all --config Project4/config.yaml
```

The command will run verification, gradient checks, the three optimization
cases, plots, report-table generation, and JSON serialization. Until the human
gate is cleared, it stops before inserting or consuming benchmark truth.

## Team

Charles Green, Christian Miranda, Lucas Somoshegyi-Szokol, and Polina
Kondratiuk.

## Immediate administrative action

The course-sheet URL milestone was November 4, 2026. The team should contact
the instructor and add the repository URL (and the Pages URL once available)
immediately.

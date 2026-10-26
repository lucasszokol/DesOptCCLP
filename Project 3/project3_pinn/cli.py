from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from .analysis import generate_analysis
from .config import ExperimentConfig
from .lbm import generate_references, grid_refinement_check, run_lbm
from .pinn import train_experiment, train_model


def _config(args: argparse.Namespace) -> ExperimentConfig:
    config = ExperimentConfig.quick(Path(args.output)) if args.quick else ExperimentConfig(output_dir=Path(args.output))
    reynolds = tuple(args.reynolds) if args.reynolds else config.reynolds_numbers
    seeds = tuple(args.seeds) if args.seeds else config.seeds
    methods = tuple(args.methods) if args.methods else config.methods
    return replace(config, reynolds_numbers=reynolds, seeds=seeds, methods=methods)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose PINN convergence for cylinder flow")
    parser.add_argument("command", choices=("reference", "train", "analyze", "all"))
    parser.add_argument("--output", default="project3_results")
    parser.add_argument("--reynolds", nargs="+", type=int)
    parser.add_argument("--seeds", nargs="+", type=int)
    parser.add_argument("--methods", nargs="+", choices=("vanilla", "balanced", "supervised"))
    parser.add_argument("--quick", action="store_true", help="Run a small smoke-test configuration")
    parser.add_argument("--force", action="store_true", help="Replace existing run artifacts")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = _config(args)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    (config.output_dir / "experiment_config.json").write_text(
        json.dumps(config.as_dict(), indent=2), encoding="utf-8"
    )
    if args.command in {"reference", "all"}:
        paths = generate_references(config, force=args.force)
        print("Generated references:", *(str(path) for path in paths), sep="\n  ")
        if not args.quick:
            print("Grid refinement:", grid_refinement_check(config, force=args.force))
    if args.command in {"train", "all"}:
        if args.command == "train":
            for reynolds in config.reynolds_numbers:
                reference = config.output_dir / "reference" / f"cylinder_re{reynolds}.npz"
                if not reference.exists():
                    run_lbm(config, reynolds)
        paths = train_experiment(config, force=args.force)
        print("Generated checkpoints:", *(str(path) for path in paths), sep="\n  ")
    if args.command in {"analyze", "all"}:
        print(json.dumps(generate_analysis(config), indent=2))
    return 0

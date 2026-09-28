"""Build the submission notebook from the report and tested analysis module."""

# Delay type-hint evaluation for compatibility with supported Python versions.
from __future__ import annotations

# JSON is the file format used by Jupyter notebooks.
import json
# Path keeps file operations independent of the operating system.
from pathlib import Path


# Every input and output file is stored beside this builder script.
ROOT = Path(__file__).resolve().parent


def markdown_sections(markdown: str) -> list[str]:
    """Split the report before each second-level Markdown heading."""

    # sections stores finished notebook cells, and current stores one cell.
    sections: list[str] = []
    current: list[str] = []
    # Keep newline characters so notebook text preserves report formatting.
    for line in markdown.splitlines(keepends=True):
        # A new ## heading starts a new notebook Markdown cell.
        if line.startswith("## ") and current:
            sections.append("".join(current).rstrip() + "\n")
            current = []
        # Add this line to the section currently being assembled.
        current.append(line)
    # Save the final section because no later heading will trigger the block.
    if current:
        sections.append("".join(current).rstrip() + "\n")
    # Return report sections in their original order.
    return sections


def markdown_cell(source: str) -> dict[str, object]:
    """Convert Markdown text to one Jupyter notebook cell dictionary."""

    # Jupyter stores cell source as a list of lines.
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code_cell(source: str) -> dict[str, object]:
    """Convert Python text to one unexecuted Jupyter code cell dictionary."""

    # Empty outputs and a null execution count mark a clean notebook cell.
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def main() -> None:
    """Combine the report and analysis calls into a runnable notebook."""

    # Read the Markdown report as the single source for the written discussion.
    report = (ROOT / "Project_2_Report.md").read_text(encoding="utf-8")
    # Split long report text into readable notebook cells.
    sections = markdown_sections(report)
    # Cells are appended in the same order in which readers see them.
    cells: list[dict[str, object]] = []

    # The first code cell imports the tested implementation and creates inputs.
    setup_code = """import numpy as np
from IPython.display import Image, display

from project2_truss import (
    analyze_ratios,
    create_truss_model,
    main as run_complete_analysis,
    verify_model,
)
from truss_config import LOADS, MEMBERS, NODES, SUPPORTS

model = create_truss_model(NODES, MEMBERS, SUPPORTS, LOADS)
ratios = np.array([1, 10, 100, 1000, 10000], dtype=float)
"""
    # This cell lets a reader recompute the complete numeric ratio sweep.
    diagnostics_code = """# Recompute D1-D4 numerical diagnostics.
records = analyze_ratios(model, ratios)
records
"""
    # This cell regenerates all figures and machine-readable output files.
    run_code = """# Regenerate all figures, CSV data, and verification output.
run_complete_analysis()
"""
    # This cell displays the independent finite element and CG checks.
    verification_code = """# Run the report's core finite element verification checks.
verification = verify_model(model)
verification
"""

    # Insert computation cells next to the report sections that discuss them.
    for index, section in enumerate(sections):
        cells.append(markdown_cell(section))
        if index == 0:
            cells.append(code_cell(setup_code))
        if section.startswith("## 3."):
            cells.append(code_cell(diagnostics_code))
        if section.startswith("## 5."):
            cells.append(code_cell(run_code))
        if section.startswith("## 6."):
            cells.append(code_cell(verification_code))

    # These required notebook fields select Python 3 and notebook format 4.
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    # Write readable JSON and use ASCII escapes for maximum file portability.
    (ROOT / "Project_2_Report.ipynb").write_text(
        json.dumps(notebook, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )


# Build the notebook only when this script is run directly.
if __name__ == "__main__":
    main()

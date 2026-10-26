"""Build a readable notebook copy of Project_3_Report.md without executing training."""

from __future__ import annotations

import json
import uuid
from pathlib import Path


def _cell_id() -> str:
    """Return a valid, stable-format notebook cell identifier."""
    return uuid.uuid4().hex[:8]


def main() -> None:
    source = Path("Project_3_Report.md").read_text(encoding="utf-8")
    cells = []
    chunks = source.split("\n```powershell\n")
    for index, chunk in enumerate(chunks):
        if index == 0:
            cells.append({"cell_type": "markdown", "id": _cell_id(), "metadata": {}, "source": chunk.splitlines(True)})
            continue
        code, remainder = chunk.split("\n```\n", 1)
        cells.append(
            {
                "cell_type": "code",
                "id": _cell_id(),
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [f"# PowerShell command (run in a terminal):\n# {line}\n" for line in code.splitlines()],
            }
        )
        cells.append({"cell_type": "markdown", "id": _cell_id(), "metadata": {}, "source": remainder.splitlines(True)})
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    Path("Project_3_Report.ipynb").write_text(json.dumps(notebook, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

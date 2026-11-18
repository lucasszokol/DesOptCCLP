"""Human-input gates required by the course brief."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml


class HumanGateError(RuntimeError):
    pass


def _load_mapping(path: Path, label: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise HumanGateError(f"Cannot read {label} at {path}: {error}") from error
    if not isinstance(data, dict):
        raise HumanGateError(f"{label} must contain a YAML mapping")
    return data


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_human_approvals(project_directory: Path) -> tuple[dict, dict]:
    approval_path = project_directory / "approvals.yaml"
    truth_path = project_directory / "tests" / "benchmark_truth.yaml"
    missing = [str(path) for path in (approval_path, truth_path) if not path.exists()]
    if missing:
        raise HumanGateError(
            "Required human-authored files are missing: " + ", ".join(missing)
        )
    approvals = _load_mapping(approval_path, "approval record")
    truth = _load_mapping(truth_path, "benchmark truth")
    if approvals.get("specification_approved") is not True:
        raise HumanGateError("specification_approved must be true")
    if not _nonempty_text(approvals.get("approver")):
        raise HumanGateError("approver name is required")
    approval_date = approvals.get("approval_date")
    if not (isinstance(approval_date, date) or _nonempty_text(approval_date)):
        raise HumanGateError("approval_date is required")
    if truth.get("status") != "student_verified":
        raise HumanGateError("benchmark truth must have status: student_verified")
    if not _nonempty_text(truth.get("student_attestation")):
        raise HumanGateError("benchmark truth requires student_attestation")
    return approvals, truth

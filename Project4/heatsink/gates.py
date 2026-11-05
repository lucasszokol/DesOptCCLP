"""Human-input gates required by the course brief."""

from __future__ import annotations

from pathlib import Path

import yaml


class HumanGateError(RuntimeError):
    pass


def require_human_approvals(project_directory: Path) -> tuple[dict, dict]:
    approval_path = project_directory / "approvals.yaml"
    truth_path = project_directory / "tests" / "benchmark_truth.yaml"
    missing = [str(path) for path in (approval_path, truth_path) if not path.exists()]
    if missing:
        raise HumanGateError(
            "Required human-authored files are missing: " + ", ".join(missing)
        )
    approvals = yaml.safe_load(approval_path.read_text(encoding="utf-8"))
    truth = yaml.safe_load(truth_path.read_text(encoding="utf-8"))
    if approvals.get("specification_approved") is not True:
        raise HumanGateError("specification_approved must be true")
    if not approvals.get("approver"):
        raise HumanGateError("approver name is required")
    if truth.get("status") != "student_verified":
        raise HumanGateError("benchmark truth must have status: student_verified")
    if not truth.get("student_attestation"):
        raise HumanGateError("benchmark truth requires student_attestation")
    return approvals, truth

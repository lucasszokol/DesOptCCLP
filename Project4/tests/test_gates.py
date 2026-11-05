from pathlib import Path

import pytest

from heatsink.gates import HumanGateError, require_human_approvals


def test_missing_human_files_stop_the_pipeline(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    with pytest.raises(HumanGateError, match="missing"):
        require_human_approvals(tmp_path)

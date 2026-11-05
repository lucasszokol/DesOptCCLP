"""Make the in-repository ``heatsink`` package importable from any test cwd."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT4 = Path(__file__).resolve().parents[1]
if str(PROJECT4) not in sys.path:
    sys.path.insert(0, str(PROJECT4))

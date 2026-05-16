"""Lightweight typing and runtime helpers used to satisfy mypy in core modules.

This module provides NumPy typing aliases and safe conversion helpers that
are intentionally minimal and have runtime checks to narrow types for mypy.

Note: ``NDArrayFloat`` and ``to_float_array`` are defined in
``fhs.core.typing_utils`` and re-exported here so that infrastructure code
can still use the short import path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Re-export from the layer-neutral core module so that:
# - infrastructure code keeps its existing import path
# - domain services use fhs.core.typing_utils (no layer violation)
from fhs.core.typing_utils import NDArrayFloat, to_float_array  # noqa: F401


def safe_json_load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def safe_yaml_load(path: Path, loader: Any) -> dict[str, Any]:
    # kept intentionally simple; callers should validate the dict shape
    with path.open("r", encoding="utf-8") as fh:
        data = loader(fh)
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML mapping in {path}")
    return data

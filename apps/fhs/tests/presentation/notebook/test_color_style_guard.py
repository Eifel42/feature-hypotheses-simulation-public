# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

"""Guardrails for color usage in notebook and plotting presentation code."""

from __future__ import annotations

import re
from pathlib import Path

_HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{3,6}")
_GENERIC_COLOR_RE = re.compile(
    r"""["'](?:white|red|green|blue|orange|gold|lightblue)["']"""
)


def _iter_guarded_files() -> list[Path]:
    root = Path(__file__).resolve().parents[3]
    src_root = root / "src" / "fhs"

    guarded_paths = [
        src_root / "presentation" / "notebook" / "charts",
        src_root / "presentation" / "notebook" / "widgets",
        src_root / "presentation" / "notebook" / "formatters.py",
        src_root / "plotting",
    ]

    files: list[Path] = []
    for path in guarded_paths:
        if path.is_file():
            files.append(path)
            continue
        files.extend(sorted(path.rglob("*.py")))

    return [f for f in files if f.name != "styling.py"]


def test_no_hardcoded_hex_or_generic_colors_in_presentation_code() -> None:
    """Ensure chart/widget/plot modules reference palette tokens instead of literals."""
    violations: list[str] = []

    for file_path in _iter_guarded_files():
        text = file_path.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            if _HEX_COLOR_RE.search(line):
                violations.append(f"{file_path}:{idx} contains hex color literal")
            if _GENERIC_COLOR_RE.search(line):
                violations.append(
                    f"{file_path}:{idx} contains generic color name literal"
                )

    assert not violations, "Color style guard violations:\n" + "\n".join(violations)

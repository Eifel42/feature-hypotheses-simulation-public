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

"""Architecture checks for notebook imports and DDD entry points."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

NOTEBOOK_ROOT = Path(__file__).resolve().parents[2] / "notebooks"
ALLOWED_NOTEBOOK_IMPORTS = {
    "fhs",
    "fhs.notebook",
    "fhs.plotting.simulation",
    "fhs.presentation.notebook",
    "fhs.presentation.notebook.charts",
    "fhs.application",
    "fhs.application.optimization_service",
}
FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+fhs\.(?:core|infra)\b", re.MULTILINE
)
FORBIDDEN_SRC_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+src\.fhs\.(?:core|infra)\b", re.MULTILINE
)
LOAD_SCENARIO_IMPORT_PATTERN = re.compile(
    r"^\s*from\s+fhs\.notebook\s+import\s+.*\bload_scenario\b", re.MULTILINE
)
DISPLAY_GLOSSARY_IMPORT_PATTERN = re.compile(
    r"^\s*from\s+fhs\.notebook\s+import\s+.*\bdisplay_glossary\b", re.MULTILINE
)
NUMPY_IMPORT_PATTERN = re.compile(r"^\s*import\s+numpy\s+as\s+np\b", re.MULTILINE)
FORBIDDEN_OUTER_LAYER_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+fhs\.(?:core|infra)\b", re.MULTILINE
)
LEGACY_NUMPY_NOTEBOOK_ALLOWLIST: set[str] = set()


def _iter_notebooks() -> list[Path]:
    return sorted(
        path
        for path in NOTEBOOK_ROOT.rglob("*.ipynb")
        if ".ipynb_checkpoints" not in path.parts
    )


def _read_code(notebook_path: Path) -> str:
    data = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells: list[str] = []
    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            code_cells.append("".join(source))
        elif isinstance(source, str):
            code_cells.append(source)
    return "\n\n".join(code_cells)


def _extract_fhs_imports(code: str) -> set[str]:
    imports: set[str] = set()
    sanitized_lines = []
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("%") or stripped.startswith("!"):
            continue
        sanitized_lines.append(line)

    tree = ast.parse("\n".join(sanitized_lines))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fhs" or alias.name.startswith("fhs."):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "fhs" or module.startswith("fhs."):
                imports.add(module)

    return imports


def test_notebooks_do_not_import_core_or_infra_directly() -> None:
    violations: list[str] = []

    for notebook_path in _iter_notebooks():
        code = _read_code(notebook_path)
        if FORBIDDEN_IMPORT_PATTERN.search(code) or FORBIDDEN_SRC_IMPORT_PATTERN.search(
            code
        ):
            relative = notebook_path.relative_to(NOTEBOOK_ROOT.parent)
            violations.append(str(relative))

    assert not violations, (
        "Notebooks must not import fhs.core.*, fhs.infra.*, src.fhs.core.*, "
        "or src.fhs.infra.* directly:\n- " + "\n- ".join(violations)
    )


def test_notebooks_only_use_allowed_fhs_entry_points() -> None:
    violations: list[str] = []

    for notebook_path in _iter_notebooks():
        code = _read_code(notebook_path)
        imports = _extract_fhs_imports(code)
        disallowed = sorted(imports - ALLOWED_NOTEBOOK_IMPORTS)
        if not disallowed:
            continue

        relative = notebook_path.relative_to(NOTEBOOK_ROOT.parent)
        violations.append(f"{relative}: {', '.join(disallowed)}")

    assert not violations, (
        "Notebooks must use only approved FHS entry points:\n- "
        + "\n- ".join(violations)
    )


def test_notebooks_use_notebook_facade_for_scenario_loading() -> None:
    violations: list[str] = []

    for notebook_path in _iter_notebooks():
        code = _read_code(notebook_path)
        if "load_scenario(" not in code:
            continue
        if LOAD_SCENARIO_IMPORT_PATTERN.search(code):
            continue
        relative = notebook_path.relative_to(NOTEBOOK_ROOT.parent)
        violations.append(str(relative))

    assert not violations, (
        "Notebooks using load_scenario(...) must import it from fhs.notebook:\n- "
        + "\n- ".join(violations)
    )


def test_notebooks_use_notebook_facade_for_glossary() -> None:
    violations: list[str] = []

    for notebook_path in _iter_notebooks():
        code = _read_code(notebook_path)
        if "display_glossary(" not in code:
            continue
        if DISPLAY_GLOSSARY_IMPORT_PATTERN.search(code):
            continue
        relative = notebook_path.relative_to(NOTEBOOK_ROOT.parent)
        violations.append(str(relative))

    assert not violations, (
        "Notebooks using display_glossary(...) must import it from fhs.notebook:\n- "
        + "\n- ".join(violations)
    )


def test_notebooks_forbid_numpy_and_outer_layers_outside_tutorials() -> None:
    violations: list[str] = []

    for notebook_path in _iter_notebooks():
        relative = notebook_path.relative_to(NOTEBOOK_ROOT.parent)
        # Tutorial notebooks are didactic exceptions by design.
        if "tutorial" in notebook_path.parts:
            continue

        code = _read_code(notebook_path)
        has_numpy = bool(NUMPY_IMPORT_PATTERN.search(code))
        has_outer = bool(
            FORBIDDEN_OUTER_LAYER_IMPORT_PATTERN.search(code)
            or FORBIDDEN_SRC_IMPORT_PATTERN.search(code)
        )

        relative_str = str(relative)
        if has_numpy and relative_str in LEGACY_NUMPY_NOTEBOOK_ALLOWLIST:
            has_numpy = False

        if has_numpy or has_outer:
            problems: list[str] = []
            if has_numpy:
                problems.append("import numpy as np")
            if has_outer:
                problems.append(
                    "fhs.core.*, fhs.infra.*, src.fhs.core.*, or src.fhs.infra.* import"
                )
            violations.append(f"{relative}: {', '.join(problems)}")

    assert not violations, (
        "Non-tutorial notebooks must not import numpy/core/infra directly:\n- "
        + "\n- ".join(violations)
    )


def test_notebook_02_feature_overview_wires_roi_column_input() -> None:
    notebook_path = NOTEBOOK_ROOT / "02-blockchain-case-study.ipynb"
    code = _read_code(notebook_path)

    assert "show.feature_overview(" in code
    assert "standalone_roi_func=case.roi" in code

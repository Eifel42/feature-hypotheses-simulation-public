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

"""Guard tests for notebook language and visibility rules.

These tests prevent language drift in the notebook collection:
- No `revenue` in primary notebook prose or labels.
- Every code cell must have ``metadata.jupyter.source_hidden = true``.

How to update the method-term allowlist
---------------------------------------
If you add a new valid financial-risk or method reference that the
``revenue`` check would incorrectly flag (it won't — the check is literal),
you do not need to change this file.

If you add a new *forbidden* term (e.g. a future deprecation), add it to
``FORBIDDEN_TERMS`` below and add an entry in the ``FORBIDDEN_TERM_EXCEPTIONS``
dict if there are specific notebooks where the term is expected as a migration note.

Method terms that are always allowed
--------------------------------------
The following terms are considered valid method or governance references and
are NOT checked by these tests:

    VaR, VaR 95%, CVaR, CVaR 95%,  Monte Carlo, NPV, IRR,
    Efficient Frontier, Profitability Index, Loss at Risk, LaR,
    Shapley Value, Break-even Probability

These terms may appear freely in any notebook.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

NOTEBOOK_ROOT = Path(__file__).resolve().parents[2] / "notebooks"

# ---------------------------------------------------------------------------
# Primary notebooks: the core learning path that Product Owners read first.
# Advanced and tutorial notebooks are included because the same language rule
# applies across the whole collection.
# ---------------------------------------------------------------------------
PRIMARY_NOTEBOOKS = [
    "01-getting-started.ipynb",
    "02-blockchain-case-study.ipynb",
    "03-blockchain-case-study-capital-budgeting.ipynb",
    "04-blockchain-case-study-advisor.ipynb",
    "05-blockchain-case-study-risk.ipynb",
    "06-blockchain-case-study-delivery-risk.ipynb",
    "07-blockchain-case-study-decision.ipynb",
    "advanced/01-portfolio-advisor.ipynb",
    "advanced/02-portfolio-risk-dashboard.ipynb",
    "tutorial/01-distribution-guide.ipynb",
    "GLOSSARY.ipynb",
    "README.ipynb",
]

# ---------------------------------------------------------------------------
# Forbidden terms: plain-text strings that must not appear in notebook prose,
# markdown, or code-cell source.
#
# Key: term string (case-sensitive)
# Value: set of notebook paths (relative to NOTEBOOK_ROOT) that are
#        explicitly allowed to contain the term (migration notes or
#        deliberately preserved historical references).
#        Leave empty set {} to forbid the term in all notebooks.
# ---------------------------------------------------------------------------
FORBIDDEN_TERMS: dict[str, set[str]] = {
    "revenue": set(),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_notebook(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_primary_notebooks() -> list[tuple[str, Path]]:
    """Return (relative_name, absolute_path) for each primary notebook.

    Fails loudly when a declared notebook is missing on disk — silent skipping
    has previously masked real renames (e.g. 07 ``best-combination`` → ``decision``).
    """
    missing = [
        name for name in PRIMARY_NOTEBOOKS if not (NOTEBOOK_ROOT / name).exists()
    ]
    if missing:
        raise FileNotFoundError(
            "PRIMARY_NOTEBOOKS lists files that do not exist under "
            f"{NOTEBOOK_ROOT}: {missing}. "
            "Update the list to match the actual filenames."
        )
    return [(name, NOTEBOOK_ROOT / name) for name in PRIMARY_NOTEBOOKS]


def _all_text_in_notebook(nb: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (cell_type, text) pairs for every markdown and code-source cell."""
    fragments = []
    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else source
        if text:
            fragments.append((cell_type, text))
    return fragments


def _code_cells(nb: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]


# Captures markdown link targets that point at a notebook file.
# Allows optional ``#anchor`` suffixes; rejects absolute URLs.
_NB_LINK_RE = re.compile(r"\]\(([^)#]+\.ipynb)(?:#[^)]*)?\)")


def _notebook_link_targets(nb: dict[str, Any]) -> list[tuple[int, str]]:
    """Return (cell_index, relative target) for every ``.ipynb`` link in markdown."""
    targets: list[tuple[int, str]] = []
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else source
        for match in _NB_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://")):
                continue
            targets.append((i, target))
    return targets


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("notebook_name,notebook_path", _iter_primary_notebooks())
def test_no_revenue_in_notebooks(notebook_name: str, notebook_path: Path) -> None:
    """Primary notebooks must not contain the word 'revenue'.

    The project language rule requires 'business value' naming throughout
    user-facing material.  If you need a migration note that explicitly
    discusses the old term, add the notebook path to
    ``FORBIDDEN_TERMS["revenue"]`` with a comment explaining the exception.
    """
    allowed_notebooks = FORBIDDEN_TERMS.get("revenue", set())
    if notebook_name in allowed_notebooks:
        pytest.skip(f"{notebook_name} is in the allowlist for 'revenue'")

    nb = _load_notebook(notebook_path)
    fragments = _all_text_in_notebook(nb)

    violations = [
        f"cell_type={ct!r}, line={i + 1}: {line!r}"
        for ct, text in fragments
        for i, line in enumerate(text.splitlines())
        if "revenue" in line
    ]

    assert not violations, (
        f"Notebook {notebook_name!r} contains forbidden term 'revenue'.\n"
        "Use 'business value' instead.\n"
        "Violations:\n  " + "\n  ".join(violations)
    )


@pytest.mark.parametrize("notebook_name,notebook_path", _iter_primary_notebooks())
def test_all_code_cells_are_source_hidden(
    notebook_name: str, notebook_path: Path
) -> None:
    """Every code cell in primary notebooks must have source_hidden = true.

    The target audience is Product Owners and Agile leaders.  They read
    outputs, not code.  All code cells must carry::

        {"jupyter": {"source_hidden": true}}

    To apply the metadata to all code cells at once::

        import json, pathlib
        nb = json.loads(pathlib.Path("notebook.ipynb").read_text())
        for c in nb["cells"]:
            if c["cell_type"] == "code":
                c.setdefault("metadata", {}).setdefault("jupyter", {})["source_hidden"] = True
        pathlib.Path("notebook.ipynb").write_text(json.dumps(nb, indent=1))
    """
    nb = _load_notebook(notebook_path)
    code_cells = _code_cells(nb)

    violations = []
    for i, cell in enumerate(code_cells):
        meta = cell.get("metadata", {})
        hidden = meta.get("jupyter", {}).get("source_hidden")
        if not hidden:
            source_preview = "".join(cell.get("source", []))[:80].replace("\n", "\\n")
            violations.append(
                f"code cell {i}: source_hidden={hidden!r}  {source_preview!r}"
            )

    assert not violations, (
        f"Notebook {notebook_name!r} has code cells without source_hidden=true.\n"
        "Fix: set metadata.jupyter.source_hidden = true on each code cell.\n"
        "Violations:\n  " + "\n  ".join(violations)
    )


@pytest.mark.parametrize("notebook_name,notebook_path", _iter_primary_notebooks())
def test_notebook_links_resolve(notebook_name: str, notebook_path: Path) -> None:
    """Every ``[label](path/to/foo.ipynb)`` link in markdown must resolve.

    Notebooks form a learning path; broken cross-links erode trust quickly
    because Product Owners click them in JupyterLab and hit a 404. This test
    walks markdown cells, extracts notebook-relative ``.ipynb`` targets, and
    fails if any target does not exist on disk.

    Absolute ``http(s)://`` links are skipped — coverage of remote URLs would
    require network access and belongs in a separate, opt-in check.
    """
    nb = _load_notebook(notebook_path)
    base = notebook_path.parent

    broken = []
    for cell_index, target in _notebook_link_targets(nb):
        resolved = (base / target).resolve()
        if not resolved.exists():
            broken.append(f"cell {cell_index}: {target!r} -> {resolved}")

    assert not broken, (
        f"Notebook {notebook_name!r} has broken intra-notebook links:\n  "
        + "\n  ".join(broken)
    )

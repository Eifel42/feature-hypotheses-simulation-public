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

"""Comparison and ranking table widgets."""

from __future__ import annotations

from typing import Any

from ...template_engine import render


def comparison_table(
    rows: list[tuple[str, float, float, float]],
    *,
    headers: tuple[str, str, str, str] = (
        "Feature",
        "Expected",
        "VaR95",
        "CVaR95",
    ),
    title: str = "Risk Comparison",
) -> str:
    """Return a comparison table for multiple features."""
    return render(
        "tables/comparison_table.html.j2",
        rows=rows,
        headers=headers,
        title=title,
    )


def ranking_table(
    rows: list[dict[str, Any]],
    *,
    title: str = "Feature Ranking",
    _columns: list[tuple[str, str, str]] | None = None,
) -> str:
    """Return a ranked feature table with traffic-light risk indicators."""
    return render(
        "tables/ranking_table.html.j2",
        rows=rows,
        title=title,
    )

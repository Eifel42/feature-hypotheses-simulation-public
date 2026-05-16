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

"""Decision-support table widgets."""

from __future__ import annotations

from ...template_engine import render
from ..cards import section_card


def backlog_table(
    features: list,
    strategy: dict,
    *,
    title: str = "Feature Backlog",
    expected_business_value_func=None,
    standalone_roi_func=None,
) -> str:
    """Display feature backlog with strategic categories."""
    if expected_business_value_func is None:

        def expected_business_value_func(feat):
            return (
                feat.expected_users
                * feat.conversion_rate
                * getattr(feat, "business_value_per_conversion", 0)
            )

    if standalone_roi_func is None:

        def standalone_roi_func(feat):
            return (
                expected_business_value_func(feat) - feat.development_cost
            ) / feat.development_cost

    rows = []
    for f in features:
        exp_rev = expected_business_value_func(f)
        roi_est = standalone_roi_func(f) * 100
        s = strategy.get(f.name, {"category": "N/A"})
        rows.append(
            {
                "feature": f,
                "category": s["category"],
                "exp_rev": exp_rev,
                "roi": roi_est,
            }
        )

    total_rev = sum(r["exp_rev"] for r in rows)
    total_cost = sum(r["feature"].development_cost for r in rows)
    portfolio_roi = (total_rev - total_cost) / total_cost * 100

    return render(
        "tables/backlog_table.html.j2",
        rows=rows,
        title=title,
        total_rev=total_rev,
        total_cost=total_cost,
        portfolio_roi=portfolio_roi,
    )


def sensitivity_table(
    rows: list[tuple[str, ...]],
    headers: tuple[str, ...],
    *,
    title: str = "Sensitivity Analysis",
    subtitle: str | None = None,
    highlight_value: str | list[str] | None = None,
) -> str:
    """Return a styled multi-column table wrapped in a section card."""
    if isinstance(highlight_value, list):
        hl_set = set(highlight_value)
    elif highlight_value:
        hl_set = {highlight_value}
    else:
        hl_set = set()
    table_html = render(
        "tables/sensitivity_table.html.j2",
        rows=rows,
        headers=headers,
        hl_set=hl_set,
    )
    return section_card(title, table_html, subtitle=subtitle)

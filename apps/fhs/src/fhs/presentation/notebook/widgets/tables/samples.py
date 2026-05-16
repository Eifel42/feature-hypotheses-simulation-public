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

"""Sample-data table widgets."""

from __future__ import annotations

from ...styling import COLORS
from .._helpers import _alternating_bg
from ..cards import section_card


def sample_table(
    headers: tuple[str, ...],
    rows: list[tuple[str, ...]],
    *,
    title: str = "Sample Data",
    description: str | None = None,
    footer: str | None = None,
) -> str:
    """Return a compact sample-data table wrapped in a section card."""
    header_html = "".join(
        f'<th style="padding:6px 10px;text-align:{"left" if i == 0 else "right"};'
        f'color:{COLORS.neutral};font-weight:700;">{h}</th>'
        for i, h in enumerate(headers)
    )
    body = ""
    for i, row in enumerate(rows):
        bg = _alternating_bg(i)
        cells = "".join(
            f'<td style="padding:6px 10px;text-align:{"left" if j == 0 else "right"};">{v}</td>'
            for j, v in enumerate(row)
        )
        body += f'<tr style="background:{bg};">{cells}</tr>'

    desc_html = (
        f'<div style="margin-bottom:10px;font-size:14px;color:{COLORS.neutral};">{description}</div>'
        if description
        else ""
    )
    footer_html = (
        f'<div style="margin-top:6px;font-size:12px;color:{COLORS.neutral};opacity:0.7;">{footer}</div>'
        if footer
        else ""
    )
    table_html = (
        f"{desc_html}"
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;margin:0 0 16px 0;border:1px solid {COLORS.border};">'
        f'<thead><tr style="background:{COLORS.surface};">{header_html}</tr></thead>'
        f"<tbody>{body}</tbody></table>"
        f"{footer_html}"
    )
    return section_card(title, table_html)

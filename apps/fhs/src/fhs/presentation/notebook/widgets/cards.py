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

"""Card-style notebook widgets."""

from __future__ import annotations

from ..styling import COLORS
from ..template_engine import render
from ._helpers import _footer_block, _risk_icon
from ._styles import card_wrapper, section_title
from .primitives import (
    EXECUTIVE_KPI_VALUE_FONT_SIZE,
    kpi_card,
    kpi_row,
)


def executive_summary_card(
    title: str,
    metrics: list[tuple[str, str, str]],
    *,
    accent: str | None = None,
    footer: str | None = None,
    value_font_size: str = EXECUTIVE_KPI_VALUE_FONT_SIZE,
) -> str:
    """Return a complete executive summary card."""
    c = accent or COLORS.primary
    cards = "".join(
        kpi_card(val, lbl, color=col, value_font_size=value_font_size)
        for val, lbl, col in metrics
    )
    footer_html = _footer_block(footer) if footer else ""
    return (
        f'<div style="{card_wrapper(accent=c)}">'
        f"{section_title(title)}"
        f"{kpi_row(cards)}{footer_html}</div>"
    )


def downside_risk_card(
    var95: float,
    cvar95: float,
    expected: float,
    *,
    title: str = "Downside Risk Summary",
) -> str:
    """Return a CVaR / downside-risk summary card."""
    cvar_gap = expected - cvar95
    cards = kpi_row(
        kpi_card(
            f"{var95:,.0f}",
            "BVF 95 % (Business Value Floor)",
            color=COLORS.danger,
        )
        + kpi_card(
            f"{cvar95:,.0f}",
            "CVaR 95 % (Worst-Case Average)",
            color=COLORS.danger,
        )
        + kpi_card(
            f"{cvar_gap:,.0f}",
            "CVaR Gap (Expected - CVaR)",
            color=COLORS.accent,
        )
    )
    footer = (
        f'<div style="background:{COLORS.surface};padding:14px 20px;'
        f'border-radius:4px;font-size:14px;color:{COLORS.neutral};">'
        f"If the worst 5 % of scenarios materialise, expect roughly "
        f"<b>{cvar95:,.0f}</b> conversions on average - "
        f"that's <b>{cvar_gap:,.0f}</b> below the expected value.</div>"
    )
    return (
        f'<div style="{card_wrapper(accent=COLORS.danger)}">'
        f'<h3 style="margin-top:0;color:{COLORS.neutral};">{title}</h3>'
        f"{cards}{footer}</div>"
    )


def feature_risk_card(
    name: str,
    expected_eur: float,
    var95_eur: float,
    risk_ratio: float,
    *,
    cvar95_eur: float = 0.0,
    icon: str = "📊",
    color: str | None = None,
) -> str:
    """Return a single feature risk card."""
    c = color or COLORS.primary
    light = _risk_icon(risk_ratio)

    return render(
        "cards/feature_risk_card.html.j2",
        name=name,
        expected_eur=expected_eur,
        var95_eur=var95_eur,
        cvar95_eur=cvar95_eur,
        risk_ratio=risk_ratio,
        icon=icon,
        color=c,
        light=light,
    )


def feature_scorecard(cards: list[str], *, title: str = "Executive Scorecard") -> str:
    """Wrap multiple feature risk cards in a scorecard container."""
    cards_html = "".join(cards)
    return (
        f'<div style="margin:20px 0;">'
        f'<h2 style="color:{COLORS.neutral};margin-bottom:15px;font-size:22px;">📊 {title}</h2>'
        f'<div style="display:flex;gap:15px;flex-wrap:wrap;">{cards_html}</div>'
        f"</div>"
    )


def portfolio_summary_card(
    expected: float,
    var95: float,
    std: float,
    *,
    cvar95: float | None = None,
    title: str = "Portfolio Summary",
) -> str:
    """Return a portfolio summary card with key metrics."""
    cvar_part = f" | CVaR 95% EUR {cvar95:,.0f}" if cvar95 is not None else ""
    return (
        f'<div style="background:{COLORS.background};padding:12px 18px;'
        f"border-radius:4px;margin:8px 0;border:1px solid {COLORS.border};"
        f'font-size:13px;"><b>{title}:</b> Expected EUR {expected:,.0f}/year | '
        f"BVF 95% EUR {var95:,.0f}/year"
        f"{cvar_part} | "
        f"Std Dev EUR {std:,.0f}</div>"
    )


def section_card(
    title: str,
    body: str,
    *,
    accent: str | None = None,
    subtitle: str | None = None,
) -> str:
    """Return a styled report section card."""
    c = accent or COLORS.primary
    sub = ""
    if subtitle:
        sub = (
            f'<div style="color:{COLORS.neutral};margin-bottom:15px;'
            f'font-size:14px;opacity:0.8;">{subtitle}</div>'
        )
    return (
        f'<div style="{card_wrapper(accent=c)};color:{COLORS.neutral};">'
        f'<h3 style="margin-top:0;color:{COLORS.neutral};font-size:20px;font-weight:bold;">{title}</h3>'
        f"{sub}{body}</div>"
    )


def formula_card(
    title: str,
    expression: str,
    *,
    result: str | None = None,
    accent: str | None = None,
) -> str:
    """Return a card displaying a calculation formula and its result."""
    c = accent or COLORS.primary
    body = (
        f'<div style="background:{COLORS.surface};padding:12px 16px;'
        f"border-radius:4px;font-family:monospace;font-size:14px;"
        f'color:{COLORS.neutral};">{expression}</div>'
    )
    if result:
        body += (
            f'<div style="margin-top:10px;font-size:22px;font-weight:bold;'
            f'color:{COLORS.secondary};">= {result}</div>'
        )
    return section_card(title, body, accent=c)


def detail_card(
    title: str,
    items: list[str],
    *,
    accent: str | None = None,
) -> str:
    """Return a card listing detail items."""
    c = accent or COLORS.secondary
    rows = "".join(
        f'<div style="padding:12px;margin:6px 0;background:{COLORS.surface};'
        f'border-radius:4px;font-size:14px;color:{COLORS.neutral};">{item}</div>'
        for item in items
    )
    return (
        f'<div style="{card_wrapper(accent=c)};color:{COLORS.neutral};">'
        f'<h3 style="margin-top:0;color:{COLORS.neutral};font-size:20px;font-weight:bold;">{title}</h3>'
        f"{rows}</div>"
    )

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

"""Pure formatting helpers for capital budgeting widgets.

Extracted from ``_capital_budgeting.py`` so they can be tested independently
and reused across multiple methods without closures.
"""

from __future__ import annotations

import math
from typing import Any


def format_cashflow(v: float, *, colors: Any) -> str:
    """Colour-coded cashflow cell — green for positive, red for negative, dash for zero."""
    if math.isclose(v, 0.0):
        return f"<span style='color:{colors.border}'>—</span>"
    color = colors.success_vivid if v >= 0 else colors.danger_vivid
    sign = "+" if v >= 0 else "−"
    return f"<span style='font-weight:700;color:{color}'>{sign}€{abs(v):,.0f}</span>"


def format_npv(v: float, *, colors: Any) -> str:
    """Bold colour-coded NPV cell."""
    color = colors.success_vivid if v >= 0 else colors.danger_vivid
    sign = "+" if v >= 0 else "−"
    return f"<span style='font-weight:800;color:{color}'>{sign}€{abs(v):,.0f}</span>"


def format_discount_factor(v: float, *, colors: Any) -> str:
    """Italic discount-factor annotation."""
    return (
        f"<span style='color:{colors.neutral};"
        f"font-style:italic;font-size:11px'>{v:.3f}</span>"
    )


def format_irr_badge(v: float | None, hurdle: float, *, colors: Any) -> str:
    """Pill badge for IRR value.

    Three tiers:
    - Green: IRR ≥ hurdle (clears cost of capital)
    - Red:   IRR < hurdle but > 0 (positive but below target)
    - Dark red + special label: IRR ≤ 0 (NPV has no positive root — never breaks even)
    """
    if v is None or math.isnan(v):
        return (
            f"<span style='display:inline-block;background:{colors.surface};"
            f"color:{colors.neutral};border:1px solid {colors.border};"
            f"padding:4px 12px;border-radius:14px;font-size:13px;"
            f"font-weight:600'>n/a</span>"
        )
    if v <= 0:
        return (
            f"<span style='display:inline-block;background:{colors.danger_vivid};"
            f"color:{colors.danger_surface};"
            f"border:1.5px solid {colors.danger_vivid};"
            f"padding:4px 12px;border-radius:14px;font-size:13px;"
            f"font-weight:700;white-space:nowrap'>≤ 0 % — no root</span>"
        )
    above = v >= hurdle
    bg = colors.success_surface if above else colors.danger_surface
    fg = colors.success_vivid if above else colors.danger_vivid
    border_color = colors.success_border if above else colors.danger_border
    return (
        f"<span style='display:inline-block;background:{bg};color:{fg};"
        f"border:1.5px solid {border_color};"
        f"padding:4px 12px;border-radius:14px;font-size:14px;"
        f"font-weight:700;white-space:nowrap'>{v:.1%}</span>"
    )


def format_irr_verdict(
    a: float | None, b: float | None, hurdle: float, *, colors: Any
) -> str:
    """One-line verdict comparing IRR A and B against the hurdle rate."""
    a_ok = a is not None and not math.isnan(a) and a >= hurdle
    b_ok = b is not None and not math.isnan(b) and b >= hurdle
    if a_ok and b_ok:
        return (
            f"<span style='color:{colors.success_vivid};font-size:12px;"
            f"font-weight:700'>Both clear hurdle · B stronger</span>"
        )
    if b_ok and not a_ok:
        return (
            f"<span style='color:{colors.warning};font-size:12px;"
            f"font-weight:700'>B clears hurdle · A does not</span>"
        )
    if a_ok and not b_ok:
        return (
            f"<span style='color:{colors.warning};font-size:12px;"
            f"font-weight:700'>A clears hurdle · B does not</span>"
        )
    return (
        f"<span style='color:{colors.danger_vivid};font-size:12px;"
        f"font-weight:700'>Both below hurdle rate</span>"
    )


def format_value_k(v: float) -> str:
    """Format a value in thousands (k) with sign — used in NPV comparison tables."""
    if math.isnan(v):
        return "—"
    sign = "+" if v >= 0 else "−"
    return f"{sign}€{abs(v) / 1_000:,.0f}k"

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

"""Shared helper functions for notebook widget HTML rendering."""

from __future__ import annotations

from ..styling import COLORS


def _risk_icon(ratio: float) -> str:
    """Return a traffic-light icon for a risk ratio."""
    if ratio < 0.20:
        return "🟢"
    if ratio < 0.40:
        return "🟡"
    return "🔴"


def _alternating_bg(idx: int) -> str:
    """Return alternating row background colour."""
    return COLORS.surface if idx % 2 else COLORS.background


def _footer_block(
    text: str,
    *,
    margin_top: str = "0",
    padding: str = "14px 20px",
    font_size: str = "16px",
    border_left_color: str | None = None,
) -> str:
    """Return a reusable footer block with optional left accent border."""
    border_left = ""
    if border_left_color:
        border_left = f"border-left:4px solid {border_left_color};"

    return (
        f'<div style="margin-top:{margin_top};background:{COLORS.surface};padding:{padding};'
        f"border-radius:4px;font-size:{font_size};{border_left}"
        f'color:{COLORS.neutral};">{text}</div>'
    )


def _cell_color(value: float) -> str:
    """Return success or danger colour based on the sign of a value."""
    return COLORS.success if value >= 0 else COLORS.danger


def _fmt_signed(value: float) -> str:
    """Format signed EUR values with explicit sign and unicode minus."""
    sign = "+" if value >= 0 else "−"
    return f"{sign}€{abs(value):,.0f}"


def _eur(value: float) -> str:
    """Format unsigned EUR values."""
    return f"€{value:,.0f}"

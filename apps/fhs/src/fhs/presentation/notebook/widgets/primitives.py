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

"""Primitive notebook widget building blocks."""

from __future__ import annotations

from ..styling import COLORS

# Unified typography defaults for executive KPI cards used across notebooks.
EXECUTIVE_KPI_VALUE_FONT_SIZE = "24px"
EXECUTIVE_KPI_LABEL_FONT_SIZE = "15px"


def info_box(text: str, *, accent: str | None = None) -> str:
    """Return an HTML info-box string (border-left accent bar)."""
    c = accent or COLORS.primary
    return (
        f'<div style="background:{COLORS.background};border:1px solid {COLORS.border};'
        f"border-left:4px solid {c};padding:12px 20px;border-radius:2px;"
        f'color:{COLORS.neutral};font-size:14px;line-height:1.5;">{text}</div>'
    )


def kpi_card(
    value: str,
    label: str,
    *,
    color: str | None = None,
    value_font_size: str = EXECUTIVE_KPI_VALUE_FONT_SIZE,
    label_font_size: str = EXECUTIVE_KPI_LABEL_FONT_SIZE,
) -> str:
    """Return HTML for a single KPI card (value + uppercase label)."""
    c = color or COLORS.secondary
    return (
        f'<div style="flex:1;min-width:150px;background:{COLORS.background};'
        f'padding:14px 16px;border-left:4px solid {c};text-align:center;">'
        f'<div style="font-size:{value_font_size};font-weight:bold;color:{c};">{value}</div>'
        f'<div style="font-size:{label_font_size};color:{COLORS.neutral};'
        f'text-transform:uppercase;font-weight:700;letter-spacing:0.02em;">{label}</div></div>'
    )


def kpi_row(*cards: str) -> str:
    """Wrap multiple KPI cards in a flex row."""
    return (
        f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin:12px 0;'
        f'font-family:-apple-system,sans-serif;">{"".join(cards)}</div>'
    )


def section_subheading(title: str) -> str:
    """Return a consistent subheading for section card bodies."""
    return (
        f'<h3 style="margin:16px 0 10px;color:{COLORS.neutral};'
        f'font-size:18px;font-weight:bold;">{title}</h3>'
    )


def note_block(text: str, *, compact: bool = False) -> str:
    """Return a neutral note block for contextual explanations."""
    margin = "10px" if compact else "16px"
    font_size = "13px" if compact else "15px"
    return (
        f'<div style="margin-top:{margin};background:{COLORS.surface};'
        f"padding:14px 20px;border-radius:4px;font-size:{font_size};"
        f'color:{COLORS.neutral};line-height:1.4;">{text}</div>'
    )


def warning_box(text: str) -> str:
    """Return an HTML warning box (amber accent)."""
    return (
        f'<div style="background:{COLORS.surface};padding:12px 18px;'
        f"border-left:4px solid {COLORS.warning};margin:6px 0;"
        f'color:{COLORS.neutral};font-size:14px;line-height:1.4;">⚠️ {text}</div>'
    )


def danger_box(text: str) -> str:
    """Return an HTML danger box (red accent)."""
    return (
        f'<div style="background:{COLORS.surface};padding:12px 18px;'
        f"border-left:4px solid {COLORS.danger};margin:6px 0;"
        f'color:{COLORS.neutral};font-size:14px;line-height:1.4;">⛔ {text}</div>'
    )


def success_box(text: str) -> str:
    """Return an HTML success box (green accent)."""
    return (
        f'<div style="background:{COLORS.surface};padding:12px 18px;'
        f"border-left:4px solid {COLORS.success};margin:6px 0;"
        f'color:{COLORS.neutral};font-size:14px;line-height:1.4;">✅ {text}</div>'
    )

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

"""Jinja2 template engine for HTML widget rendering.

Central environment with CSS helpers as globals and custom filters.
All templates inherit COLORS and style functions without context passing.
"""

from __future__ import annotations

import math

from jinja2 import Environment, PackageLoader
from markupsafe import Markup

from .styling import COLORS

# noinspection PyProtectedMember
from .widgets._helpers import _alternating_bg, _footer_block, _risk_icon

# noinspection PyProtectedMember
from .widgets._styles import (
    card_wrapper,
    flex_row,
    grid_layout,
    label_style,
    section_title,
    table_base,
    table_caption,
    table_header_row,
    text_style,
)

env = Environment(
    loader=PackageLoader("fhs.presentation.notebook", "templates"),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _safe(fn):
    """Wrap a function so its return value is marked as safe HTML."""

    def wrapper(*args, **kwargs):
        return Markup(fn(*args, **kwargs))

    wrapper.__name__ = fn.__name__
    return wrapper


# CSS helpers + COLORS as globals — available in every template
# Functions returning HTML are wrapped with _safe to prevent double-escaping
env.globals.update(
    COLORS=COLORS,
    card_wrapper=card_wrapper,
    table_base=table_base,
    table_caption=_safe(table_caption),
    table_header_row=_safe(table_header_row),
    section_title=_safe(section_title),
    flex_row=flex_row,
    text_style=text_style,
    label_style=label_style,
    grid_layout=grid_layout,
    alternating_bg=_alternating_bg,
    risk_icon=_risk_icon,
    footer_block=_safe(_footer_block),
)


def _eur(value: float) -> str:
    """Format as EUR currency."""
    return f"EUR {value:,.0f}"


def _pct(value: float) -> str:
    """Format as percentage (auto-detect 0-1 vs 0-100 range)."""
    if abs(value) <= 2.0:
        return f"{value:.0%}"
    return f"{value:.0f}%"


def _pct1(value: float) -> str:
    """Format as percentage with 1 decimal."""
    return f"{value:.1f}%"


def _signed_pct(value: float) -> str:
    """Format as signed percentage."""
    return f"{value:+.1f}%"


def _thousands(value: float) -> str:
    """Format with thousand separators."""
    return f"{value:,.0f}"


env.filters["eur"] = _eur
env.filters["pct"] = _pct
env.filters["pct1"] = _pct1
env.filters["signed_pct"] = _signed_pct
env.filters["thousands"] = _thousands

env.tests["nan"] = math.isnan


def render(template_name: str, **context: object) -> str:
    """Render a Jinja2 template with given context.

    CSS helpers and COLORS are available as globals in all templates.
    Widget-specific data is passed via context.
    """
    return env.get_template(template_name).render(**context)

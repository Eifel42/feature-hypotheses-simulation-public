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

from __future__ import annotations

from src.fhs.presentation.notebook.styling import COLORS

# noinspection PyProtectedMember
from src.fhs.presentation.notebook.widgets._styles import (
    border_style,
    card_wrapper,
    flex_column,
    flex_row,
    grid_layout,
    label_style,
    responsive_text,
    section_title,
    shadow_style,
    spacing,
    table_base,
    table_caption,
    table_data_row,
    table_header_row,
    text_style,
    transition_style,
    truncate_text,
)


def test_card_wrapper_still_works() -> None:
    result = card_wrapper(accent=COLORS.primary, padding="24px")
    assert "background:white" in result
    assert "padding:24px" in result
    assert "border-left:6px solid" in result
    assert "<" not in result


def test_table_base_still_works() -> None:
    result = table_base(font_size="13px", border=f"1px solid {COLORS.border}")
    assert "width:100%" in result
    assert "font-size:13px" in result
    assert "border:1px solid" in result
    assert "<" not in result


def test_table_caption_and_header_row_return_html() -> None:
    caption = table_caption("Metrics")
    header = table_header_row(["A", "B"])
    assert caption.startswith("<caption")
    assert header.startswith("<thead>")


def test_table_data_row_contains_alternating_background() -> None:
    row = table_data_row(["A", "B"], idx=1)
    assert row.startswith("<tr")
    assert "background:" in row


def test_section_title_returns_html() -> None:
    html = section_title("Risk", font_size="20px")
    assert html.startswith("<h2")
    assert "font-size:20px" in html


def test_flex_helpers_return_css_strings() -> None:
    row = flex_row()
    col = flex_column(gap="8px")
    assert "display:flex" in row
    assert "flex-direction:row" in row
    assert "display:flex" in col
    assert "flex-direction:column" in col
    assert "<" not in row
    assert "<" not in col


def test_grid_layout_returns_css_string() -> None:
    result = grid_layout(columns="repeat(3, 1fr)", gap="10px")
    assert "display:grid" in result
    assert "grid-template-columns:repeat(3, 1fr)" in result
    assert "<" not in result


def test_text_style_defaults_and_custom_color() -> None:
    default = text_style()
    custom = text_style(size="16px", weight="bold", color=COLORS.danger)
    assert f"color:{COLORS.neutral}" in default
    assert "font-size:16px" in custom
    assert "font-weight:bold" in custom
    assert f"color:{COLORS.danger}" in custom


def test_label_style() -> None:
    result = label_style(size="10px", transform="none")
    assert "font-size:10px" in result
    assert "text-transform:none" in result


def test_spacing_empty_and_combinations() -> None:
    assert spacing() == ""
    only_padding = spacing(padding="12px")
    both = spacing(padding="12px", margin="8px 0")
    assert "padding:12px" in only_padding
    assert "margin" not in only_padding
    assert "padding:12px" in both
    assert "margin:8px 0" in both


def test_border_style() -> None:
    result = border_style(width="2px", color=COLORS.border, radius="8px")
    assert "border:2px solid" in result
    assert "border-radius:8px" in result


def test_shadow_style_transition_and_truncate() -> None:
    shadow = shadow_style(y="4px", blur="12px")
    transition = transition_style(properties="opacity", duration="0.3s")
    trunc = truncate_text(max_width="150px")
    assert "box-shadow:" in shadow
    assert "transition:opacity 0.3s" in transition
    assert "text-overflow:ellipsis" in trunc


def test_responsive_text() -> None:
    result = responsive_text(base_size="16px", scale_factor="1.5")
    assert result.startswith("font-size:clamp(")

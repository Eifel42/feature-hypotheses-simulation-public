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

"""Shared CSS style helpers for HTML widget generation.

This module provides DRY helpers for common CSS patterns used across
card, table, and portfolio widgets. All functions return inline style strings.
"""

from __future__ import annotations

from ..styling import COLORS


def card_wrapper(
    *,
    accent: str | None = None,
    padding: str = "30px",
) -> str:
    """Return inline CSS for a standard card container.

    Args:
        accent: Optional left-border accent color (6px solid).
        padding: Inner padding, defaults to "30px".

    Returns:
        Complete inline style string for a white card with border.

    Example:
        >>> card_wrapper(accent=COLORS.primary, padding="25px")
        'background:white;border-radius:4px;padding:25px;...'
    """
    base = (
        f"background:white;border-radius:4px;padding:{padding};"
        f"border:1px solid {COLORS.border};margin:12px 0;"
        f"font-family:-apple-system,sans-serif;"
        f"box-sizing:border-box;overflow-wrap:break-word;min-width:0;"
    )
    if accent:
        base += f"border-left:6px solid {accent};"
    return base


def table_base(
    *,
    font_size: str = "14px",
    margin: str = "12px 0",
    border: str | None = None,
) -> str:
    """Return inline CSS for a standard table element.

    Args:
        font_size: Text size, defaults to "14px".
        margin: Outer margin, defaults to "12px 0".
        border: Optional border style (e.g., f"1px solid {COLORS.border}").

    Returns:
        Complete inline style string for a collapsed table.

    Example:
        >>> table_base(font_size="13px", border=f"1px solid {COLORS.border}")
        'width:100%;border-collapse:collapse;font-size:13px;...'
    """
    style = (
        f"width:100%;border-collapse:collapse;"
        f"font-size:{font_size};margin:{margin};color:{COLORS.neutral};"
    )
    if border:
        style += f"border:{border};"
    return style


def table_caption(
    text: str,
    *,
    font_weight: str = "700",
    padding: str = "6px 0",
    font_size: str = "15px",
) -> str:
    """Return complete <caption> element for table title.

    Args:
        text: Caption text content.
        font_weight: Weight value (e.g., "700", "bold"), defaults to "700".
        padding: Inner padding, defaults to "6px 0".
        font_size: Text size, defaults to "15px".

    Returns:
        Complete <caption> HTML tag with inline styling.

    Example:
        >>> table_caption("Risk Metrics", font_weight="600")
        '<caption style="text-align:left;...">Risk Metrics</caption>'
    """
    return (
        f'<caption style="text-align:left;font-weight:{font_weight};'
        f'padding:{padding};font-size:{font_size};color:{COLORS.neutral};">'
        f"{text}</caption>"
    )


def table_header_row(
    columns: list[str],
    *,
    padding: str = "12px",
    text_align: str = "left",
) -> str:
    """Return complete <tr> with <th> elements for table header.

    Args:
        columns: List of header cell texts.
        padding: Cell padding, defaults to "12px".
        text_align: Horizontal alignment, defaults to "left".

    Returns:
        Complete HTML string with styled <thead><tr>...</tr></thead>.

    Example:
        >>> table_header_row(["Metric", "Value"])
        '<thead><tr style="background:{COLORS.surface};..."><th>...</th></tr></thead>'
    """
    cells = "".join(
        f'<th style="padding:{padding};text-align:{text_align};color:{COLORS.neutral};">{col}</th>'
        for col in columns
    )
    return f'<thead><tr style="background:{COLORS.surface};">{cells}</tr></thead>'


def table_data_row(
    cells: list[str],
    idx: int,
    *,
    padding: str = "10px",
) -> str:
    """Return complete <tr> with <td> elements for table data row.

    Args:
        cells: List of cell HTML content (pre-formatted).
        idx: Row index for alternating background color.
        padding: Cell padding, defaults to "10px".

    Returns:
        Complete HTML string with styled <tr>...</tr>.

    Example:
        >>> table_data_row(["<b>Metric</b>", "123"], idx=0)
        '<tr style="background:white;"><td>...</td></tr>'
    """
    # Import here to avoid circular dependency
    from ._helpers import _alternating_bg

    bg = _alternating_bg(idx)
    td_elements = "".join(
        f'<td style="padding:{padding};">{cell}</td>' for cell in cells
    )
    return f'<tr style="background:{bg};">{td_elements}</tr>'


def section_title(
    text: str,
    *,
    color: str | None = None,
    font_size: str = "24px",
    margin: str = "0",
) -> str:
    """Return complete <h2> element for section heading.

    Args:
        text: Heading text content.
        color: Optional text color, defaults to COLORS.neutral.
        font_size: Text size, defaults to "24px".
        margin: Outer margin, defaults to "0".

    Returns:
        Complete <h2> HTML tag with inline styling.

    Example:
        >>> section_title("Risk Analysis", font_size="20px")
        '<h2 style="margin:0;color:{COLORS.neutral};font-size:20px;">Risk Analysis</h2>'
    """
    c = color or COLORS.neutral
    return f'<h2 style="margin:{margin};color:{c};font-size:{font_size};">{text}</h2>'


# Layout Helpers


def flex_row(
    *,
    gap: str = "12px",
    align_items: str = "center",
    justify_content: str = "flex-start",
    wrap: str = "nowrap",
) -> str:
    """Return inline CSS for flexbox row layout.

    Args:
        gap: Space between flex items, defaults to "12px".
        align_items: Vertical alignment, defaults to "center".
        justify_content: Horizontal alignment, defaults to "flex-start".
        wrap: Flex wrap behavior, defaults to "nowrap".

    Returns:
        Complete inline style string for flexbox row.

    Example:
        >>> flex_row(gap="20px", justify_content="space-between")
        'display:flex;flex-direction:row;gap:20px;align-items:center;...'
    """
    return (
        f"display:flex;flex-direction:row;gap:{gap};"
        f"align-items:{align_items};justify-content:{justify_content};"
        f"flex-wrap:{wrap};"
    )


def flex_column(
    *,
    gap: str = "12px",
    align_items: str = "stretch",
    justify_content: str = "flex-start",
) -> str:
    """Return inline CSS for flexbox column layout.

    Args:
        gap: Space between flex items, defaults to "12px".
        align_items: Horizontal alignment, defaults to "stretch".
        justify_content: Vertical alignment, defaults to "flex-start".

    Returns:
        Complete inline style string for flexbox column.

    Example:
        >>> flex_column(gap="16px", align_items="center")
        'display:flex;flex-direction:column;gap:16px;align-items:center;...'
    """
    return (
        f"display:flex;flex-direction:column;gap:{gap};"
        f"align-items:{align_items};justify-content:{justify_content};"
    )


def grid_layout(
    *,
    columns: str = "1fr 1fr",
    gap: str = "16px",
    align_items: str = "start",
) -> str:
    """Return inline CSS for CSS Grid layout.

    Args:
        columns: Grid template columns, defaults to "1fr 1fr" (2 equal columns).
        gap: Grid gap, defaults to "16px".
        align_items: Vertical alignment of grid items, defaults to "start".

    Returns:
        Complete inline style string for CSS Grid.

    Example:
        >>> grid_layout(columns="repeat(3, 1fr)", gap="20px")
        'display:grid;grid-template-columns:repeat(3, 1fr);gap:20px;...'
    """
    return (
        f"display:grid;grid-template-columns:{columns};"
        f"gap:{gap};align-items:{align_items};"
    )


# Typography Helpers


def text_style(
    *,
    size: str = "14px",
    weight: str = "normal",
    color: str | None = None,
    line_height: str = "1.5",
) -> str:
    """Return inline CSS for text styling.

    Args:
        size: Font size, defaults to "14px".
        weight: Font weight (e.g., "normal", "bold", "600"), defaults to "normal".
        color: Text color, defaults to COLORS.neutral.
        line_height: Line height, defaults to "1.5".

    Returns:
        Complete inline style string for text.

    Example:
        >>> text_style(size="16px", weight="bold", color=COLORS.neutral)
        'font-size:16px;font-weight:bold;color:{COLORS.neutral};line-height:1.5;'
    """
    c = color or COLORS.neutral
    return f"font-size:{size};font-weight:{weight};color:{c};line-height:{line_height};"


def label_style(
    *,
    size: str = "11px",
    transform: str = "uppercase",
) -> str:
    """Return inline CSS for small label text (KPI captions, etc.).

    Args:
        size: Font size, defaults to "11px".
        transform: Text transform, defaults to "uppercase".

    Returns:
        Complete inline style string for label text.
    """
    return (
        f"font-size:{size};color:{COLORS.neutral};font-weight:bold;"
        f"text-transform:{transform};"
    )


def responsive_text(
    *,
    base_size: str = "14px",
    scale_factor: str = "1.2",
) -> str:
    """Return inline CSS for responsive text sizing using clamp().

    Args:
        base_size: Minimum font size, defaults to "14px".
        scale_factor: Scale multiplier for max size, defaults to "1.2".

    Returns:
        Complete inline style string with clamp() for fluid typography.

    Example:
        >>> responsive_text(base_size="16px", scale_factor="1.5")
        'font-size:clamp(16px, 2vw, 24px);'
    """
    base_value = float(base_size.replace("px", ""))
    max_value = int(base_value * float(scale_factor))
    return f"font-size:clamp({base_size}, 2vw, {max_value}px);"


def truncate_text(
    *,
    max_width: str = "200px",
) -> str:
    """Return inline CSS for single-line text truncation with ellipsis.

    Args:
        max_width: Maximum width before truncation, defaults to "200px".

    Returns:
        Complete inline style string for text overflow handling.

    Example:
        >>> truncate_text(max_width="150px")
        'max-width:150px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
    """
    return (
        f"max-width:{max_width};white-space:nowrap;"
        f"overflow:hidden;text-overflow:ellipsis;"
    )


# Spacing & Effects Helpers


def spacing(
    *,
    padding: str | None = None,
    margin: str | None = None,
) -> str:
    """Return inline CSS for padding and/or margin.

    Args:
        padding: Padding value (e.g., "10px", "10px 20px"), defaults to None.
        margin: Margin value (e.g., "10px 0"), defaults to None.

    Returns:
        Inline style string with padding and/or margin.

    Example:
        >>> spacing(padding="20px", margin="12px 0")
        'padding:20px;margin:12px 0;'
    """
    parts = []
    if padding:
        parts.append(f"padding:{padding};")
    if margin:
        parts.append(f"margin:{margin};")
    return "".join(parts)


def border_style(
    *,
    width: str = "1px",
    style: str = "solid",
    color: str | None = None,
    radius: str | None = None,
) -> str:
    """Return inline CSS for border styling.

    Args:
        width: Border width, defaults to "1px".
        style: Border style (e.g., "solid", "dashed"), defaults to "solid".
        color: Border color, defaults to COLORS.border.
        radius: Optional border radius (e.g., "4px"), defaults to None.

    Returns:
        Complete inline style string for borders.

    Example:
        >>> border_style(width="2px", color=COLORS.border, radius="8px")
        'border:2px solid {COLORS.border};border-radius:8px;'
    """
    c = color or COLORS.border
    result = f"border:{width} {style} {c};"
    if radius:
        result += f"border-radius:{radius};"
    return result


def shadow_style(
    *,
    x: str = "0",
    y: str = "2px",
    blur: str = "8px",
    spread: str = "0",
    color: str = "rgba(0,0,0,0.1)",
) -> str:
    """Return inline CSS for box shadow.

    Args:
        x: Horizontal offset, defaults to "0".
        y: Vertical offset, defaults to "2px".
        blur: Blur radius, defaults to "8px".
        spread: Spread radius, defaults to "0".
        color: Shadow color, defaults to "rgba(0,0,0,0.1)".

    Returns:
        Complete inline style string for box-shadow.

    Example:
        >>> shadow_style(y="4px", blur="12px", color="rgba(0,0,0,0.15)")
        'box-shadow:0 4px 12px 0 rgba(0,0,0,0.15);'
    """
    return f"box-shadow:{x} {y} {blur} {spread} {color};"


def transition_style(
    *,
    properties: str = "all",
    duration: str = "0.2s",
    timing: str = "ease-in-out",
) -> str:
    """Return inline CSS for transition effects.

    Args:
        properties: CSS properties to transition (e.g., "all", "opacity, transform").
        duration: Transition duration, defaults to "0.2s".
        timing: Timing function, defaults to "ease-in-out".

    Returns:
        Complete inline style string for transitions.

    Example:
        >>> transition_style(properties="opacity, transform", duration="0.3s")
        'transition:opacity, transform 0.3s ease-in-out;'
    """
    return f"transition:{properties} {duration} {timing};"

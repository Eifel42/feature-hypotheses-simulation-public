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

import pytest

import src.fhs.presentation.notebook.styling as styling_module

# noinspection PyProtectedMember
from src.fhs.presentation.notebook.charts._helpers import _contrast_ratio
from src.fhs.presentation.notebook.styling import (
    COLORS,
    DARK_PALETTE,
    LIGHT_PALETTE,
    ThemeContext,
    palette,
    setup_style,
    theme,
)


def test_default_theme_is_light() -> None:
    ctx = ThemeContext()
    assert ctx.COLORS.background == LIGHT_PALETTE.background


def test_switch_to_dark_mode() -> None:
    ctx = ThemeContext()
    ctx.set_theme("dark")
    assert ctx.COLORS.background == DARK_PALETTE.background
    ctx.set_theme("light")
    assert ctx.COLORS.background == LIGHT_PALETTE.background


def test_proxy_delegates_dynamically() -> None:
    original = theme.COLORS.background
    theme.set_theme("dark")
    assert COLORS.background == DARK_PALETTE.background
    theme.set_theme("light")
    assert COLORS.background == LIGHT_PALETTE.background
    # restore current state for isolation if needed
    if original == DARK_PALETTE.background:
        theme.set_theme("dark")


def test_palette_mapping_remains_functional() -> None:
    theme.set_theme("dark")
    assert palette["primary"] == DARK_PALETTE.primary
    assert palette["background"] == DARK_PALETTE.background
    theme.set_theme("light")
    assert palette["primary"] == LIGHT_PALETTE.primary


def test_palette_mapping_exposes_heatmap_tokens() -> None:
    keys = set(palette)
    expected = {
        "heatmap_label_text",
        "heatmap_loss_deep",
        "heatmap_loss_mid",
        "heatmap_loss_soft",
        "heatmap_break_even",
        "heatmap_profit_soft",
        "heatmap_profit_mid",
        "heatmap_profit_deep",
    }

    assert expected <= keys
    assert len(palette) >= len(expected)
    for key in expected:
        assert palette[key].startswith("#")


def test_palette_mapping_rejects_unknown_key() -> None:
    with pytest.raises(KeyError, match="does_not_exist"):
        palette["does_not_exist"]


def test_setup_style_color_theme_dark() -> None:
    """setup_style(color_theme='dark') activates the dark palette."""
    setup_style(color_theme="dark")
    assert palette["background"] == DARK_PALETTE.background
    # Restore
    setup_style(color_theme="light")


def test_setup_style_auto_uses_detected_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(styling_module, "_detect_jupyter_theme", lambda: "dark")
    setup_style(color_theme="auto")
    assert palette["background"] == DARK_PALETTE.background
    setup_style(color_theme="light")


def test_setup_style_falls_back_for_unknown_style() -> None:
    setup_style(style="does-not-exist", color_theme="light")
    assert palette["background"] == LIGHT_PALETTE.background


def test_setup_style_color_theme_light() -> None:
    """setup_style(color_theme='light') restores the light palette."""
    setup_style(color_theme="dark")
    setup_style(color_theme="light")
    assert palette["background"] == LIGHT_PALETTE.background


def test_setup_style_no_theme_preserves_current() -> None:
    """setup_style() without color_theme preserves whatever is active."""
    setup_style(color_theme="dark")
    setup_style()  # no theme argument — should stay dark
    assert palette["background"] == DARK_PALETTE.background
    # Restore
    setup_style(color_theme="light")


def test_dark_palette_wcag_aa_contrast() -> None:
    text_fields = [
        "primary",
        "secondary",
        "neutral",
        "danger",
        "warning",
        "success",
        "accent",
    ]
    for field in text_fields:
        color = getattr(DARK_PALETTE, field)
        ratio = _contrast_ratio(color, DARK_PALETTE.background)
        assert ratio >= 4.5, f"{field} ({color}): {ratio:.2f}:1 < 4.5:1"

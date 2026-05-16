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

"""Tests for capital budgeting formatter functions."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

# noinspection PyProtectedMember
from src.fhs.presentation.notebook.widgets._capital_budgeting_formatters import (
    format_cashflow,
    format_discount_factor,
    format_irr_badge,
    format_irr_verdict,
    format_npv,
    format_value_k,
)


@pytest.fixture
def colors():
    return SimpleNamespace(
        success="#00c853",
        danger="#d50000",
        warning="#ff6d00",
        neutral="#546e7a",
        border="#cfd8dc",
        surface="#f5f5f5",
        background="#ffffff",
        success_vivid="#0d652d",
        danger_vivid="#a50e0e",
        success_surface="#e6f4ea",
        danger_surface="#fce8e6",
        success_border="#34a853",
        danger_border="#ea4335",
    )


class TestFormatCashflow:
    def test_zero_returns_dash(self, colors):
        result = format_cashflow(0.0, colors=colors)
        assert "—" in result
        assert colors.border in result

    def test_positive_is_green_with_plus(self, colors):
        result = format_cashflow(50_000.0, colors=colors)
        assert colors.success_vivid in result
        assert "+" in result
        assert "50,000" in result

    def test_negative_is_red_with_minus(self, colors):
        result = format_cashflow(-25_000.0, colors=colors)
        assert colors.danger_vivid in result
        assert "−" in result
        assert "25,000" in result

    def test_bold_font_weight(self, colors):
        result = format_cashflow(1.0, colors=colors)
        assert "font-weight:700" in result


class TestFormatNpv:
    def test_positive_green(self, colors):
        result = format_npv(100_000.0, colors=colors)
        assert colors.success_vivid in result
        assert "+" in result
        assert "100,000" in result

    def test_negative_red(self, colors):
        result = format_npv(-50_000.0, colors=colors)
        assert colors.danger_vivid in result
        assert "−" in result

    def test_bold_font_weight_700(self, colors):
        result = format_npv(1.0, colors=colors)
        assert "font-weight:800" in result


class TestFormatDiscountFactor:
    def test_three_decimal_places(self, colors):
        result = format_discount_factor(0.9091, colors=colors)
        assert "0.909" in result

    def test_italic_style(self, colors):
        result = format_discount_factor(1.0, colors=colors)
        assert "font-style:italic" in result
        assert colors.neutral in result


class TestFormatIrrBadge:
    def test_none_returns_na(self, colors):
        result = format_irr_badge(None, hurdle=0.08, colors=colors)
        assert "n/a" in result

    def test_nan_returns_na(self, colors):
        result = format_irr_badge(float("nan"), hurdle=0.08, colors=colors)
        assert "n/a" in result

    def test_above_hurdle_green(self, colors):
        result = format_irr_badge(0.15, hurdle=0.08, colors=colors)
        assert colors.success_vivid in result
        assert "15.0%" in result

    def test_below_hurdle_red(self, colors):
        result = format_irr_badge(0.05, hurdle=0.08, colors=colors)
        assert colors.danger_vivid in result
        assert "5.0%" in result

    def test_exactly_at_hurdle_is_green(self, colors):
        result = format_irr_badge(0.08, hurdle=0.08, colors=colors)
        assert colors.success_vivid in result

    def test_pill_badge_styling(self, colors):
        result = format_irr_badge(0.1, hurdle=0.08, colors=colors)
        assert "border-radius:14px" in result
        assert "font-weight:700" in result


class TestFormatIrrVerdict:
    def test_both_above_hurdle(self, colors):
        result = format_irr_verdict(0.15, 0.20, hurdle=0.08, colors=colors)
        assert "Both clear hurdle" in result
        assert colors.success_vivid in result

    def test_only_b_above(self, colors):
        result = format_irr_verdict(0.05, 0.15, hurdle=0.08, colors=colors)
        assert "B clears hurdle" in result
        assert "A does not" in result
        assert colors.warning in result

    def test_only_a_above(self, colors):
        result = format_irr_verdict(0.15, 0.05, hurdle=0.08, colors=colors)
        assert "A clears hurdle" in result
        assert "B does not" in result
        assert colors.warning in result

    def test_both_below(self, colors):
        result = format_irr_verdict(0.03, 0.05, hurdle=0.08, colors=colors)
        assert "Both below hurdle rate" in result
        assert colors.danger_vivid in result

    def test_none_a_treated_as_below(self, colors):
        result = format_irr_verdict(None, 0.15, hurdle=0.08, colors=colors)
        assert "B clears hurdle" in result

    def test_nan_b_treated_as_below(self, colors):
        result = format_irr_verdict(0.15, float("nan"), hurdle=0.08, colors=colors)
        assert "A clears hurdle" in result


class TestFormatValueK:
    def test_positive_value(self):
        result = format_value_k(100_000.0)
        assert "+€100k" in result

    def test_negative_value(self):
        result = format_value_k(-50_000.0)
        assert "−€50k" in result

    def test_zero(self):
        result = format_value_k(0.0)
        assert "+€0k" in result

    def test_nan_returns_dash(self):
        result = format_value_k(float("nan"))
        assert result == "—"

    def test_large_value_formatted_with_thousands_sep(self):
        result = format_value_k(1_500_000.0)
        assert "1,500k" in result

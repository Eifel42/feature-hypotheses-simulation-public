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

# noinspection PyProtectedMember
from src.fhs.presentation.notebook.charts._helpers import _contrast_ratio
from src.fhs.presentation.notebook.styling import COLORS
from src.fhs.presentation.notebook.widgets.primitives import (
    info_box,
    kpi_card,
    warning_box,
)
from src.fhs.presentation.notebook.widgets.tables import metric_table, ranking_table


def parse_inline_styles(style_str: str) -> dict[str, str]:
    return {
        key.strip().lower(): value.strip()
        for item in style_str.split(";")
        if ":" in item
        for key, value in [item.split(":", 1)]
    }


def assert_style_contains(element, **expected_styles: str) -> None:
    actual = parse_inline_styles(element.get("style", ""))
    for key, value in expected_styles.items():
        css_key = key.replace("_", "-")
        assert css_key in actual
        assert value in actual[css_key]


def test_info_box_structure(parse_html) -> None:
    html = info_box("Test message", accent=COLORS.danger)
    soup = parse_html(html)
    div = soup.find("div")
    assert div is not None
    assert "Test message" in div.get_text()
    assert_style_contains(div, border_left=f"4px solid {COLORS.danger}")


def test_kpi_card_has_value_and_label(parse_html) -> None:
    html = kpi_card("EUR 500,000", "Budget")
    soup = parse_html(html)
    value = soup.find("div", string=lambda s: s and "EUR" in s)
    label = soup.find("div", string="Budget")
    assert value is not None
    assert label is not None


def test_kpi_card_supports_custom_value_font_size(parse_html) -> None:
    html = kpi_card("EUR 500,000", "Budget", value_font_size="34px")
    soup = parse_html(html)
    value = soup.find("div", string=lambda s: s and "EUR" in s)
    assert value is not None
    assert_style_contains(value, font_size="34px")


def test_metric_table_has_semantic_headers(parse_html) -> None:
    html = metric_table([("VaR 95%", "EUR 120,000", None)])
    soup = parse_html(html)
    headers = soup.find_all("th")
    assert len(headers) >= 2


def test_metric_table_alternating_backgrounds(parse_html) -> None:
    rows = [("A", "1", None), ("B", "2", None), ("C", "3", None)]
    html = metric_table(rows)
    soup = parse_html(html)
    body_rows = soup.find("tbody").find_all("tr")
    backgrounds = [
        parse_inline_styles(tr.get("style", "")).get("background", "")
        for tr in body_rows
    ]
    assert len(set(backgrounds)) >= 2


def test_ranking_table_semantics(parse_html) -> None:
    html = ranking_table(
        [
            {
                "feature": "Feature A",
                "expected_business_value": 100000.0,
                "var_95_business_value": 80000.0,
                "risk_ratio": 0.2,
            }
        ]
    )
    soup = parse_html(html)
    assert soup.find("table") is not None
    assert soup.find("th", string=lambda s: s and "Feature" in s) is not None


def test_color_contrast_in_info_box(parse_html) -> None:
    html = info_box("Contrast")
    soup = parse_html(html)
    div = soup.find("div")
    assert div is not None
    styles = parse_inline_styles(div.get("style", ""))
    bg = styles.get("background", COLORS.background)
    text = styles.get("color", COLORS.neutral)
    assert _contrast_ratio(bg, text) >= 4.5


def test_warning_box_semantics(parse_html) -> None:
    html = warning_box("Check threshold")
    soup = parse_html(html)
    div = soup.find("div")
    assert div is not None
    assert "Check threshold" in div.get_text()
    assert "⚠️" in div.get_text()

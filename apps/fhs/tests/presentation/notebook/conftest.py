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

from typing import Any

import pytest
from bs4 import BeautifulSoup


def parse_inline_styles(style_str: str) -> dict[str, str]:
    """Parse inline style string into a normalized style dictionary."""
    return {
        key.strip().lower(): value.strip()
        for item in style_str.split(";")
        if ":" in item
        for key, value in [item.split(":", 1)]
    }


def assert_style_contains(element: Any, **expected_styles: str) -> None:
    """Assert that a tag contains expected inline CSS fragments."""
    actual = parse_inline_styles(element.get("style", ""))
    for key, value in expected_styles.items():
        css_key = key.replace("_", "-")
        assert css_key in actual, f"Style '{css_key}' not found in {actual}"
        assert value in actual[css_key], (
            f"Style '{css_key}': expected '{value}' in '{actual[css_key]}'"
        )


@pytest.fixture
def parse_html():
    """Parse HTML snippet into BeautifulSoup."""

    def _parse(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    return _parse

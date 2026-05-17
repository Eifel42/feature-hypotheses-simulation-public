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

"""
Tests for notebook glossary loading utilities.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from fhs.notebook import load_glossary

# noinspection PyProtectedMember
from fhs.notebook.glossary import (
    _clean_definition,
    _extract_term_heading,
    _normalize_text,
    _parse_glossary_lines,
    _raw_lines_from_path,
    _should_skip_glossary_line,
    _term_matches_tokens,
    display_glossary,
    glossary_widget,
)


def test_load_glossary_default_contains_core_terms():
    """Default glossary load returns expected columns and key terms."""
    df = load_glossary()

    assert list(df.columns) == ["Section", "Term", "Definition"]
    assert len(df) > 0
    assert any(df["Term"].str.contains("Monte Carlo Simulation", regex=False))
    assert any(
        df["Term"].str.contains("VaR 95%", regex=False)
        | df["Term"].str.contains("Business Value Floor", regex=False)
    )


def test_load_glossary_term_filter_restricts_rows():
    """Term filtering should return only matching glossary entries."""
    terms = ["Sharpe Ratio", "Efficient Frontier", "Budget Optimizer"]
    df = load_glossary(include_terms=terms)

    assert len(df) >= 3
    assert any(df["Term"].str.contains("Sharpe Ratio", regex=False))
    assert any(df["Term"].str.contains("Efficient Frontier", regex=False))
    assert any(df["Term"].str.contains("Budget Optimizer", regex=False))


def test_load_glossary_contains_advanced_notebook_terms():
    """Central glossary should cover advanced notebook glossary slices."""
    terms = [
        "Exact Solver",
        "ILP Solver",
        "Delivery Risk / Bernoulli Gate (Level 2)",
        "Systematic Shock (Level 3)",
        "Business Value per Conversion",
    ]

    df = load_glossary(include_terms=terms)

    assert len(df) >= len(terms)
    for term in terms:
        assert any(df["Term"].str.contains(term, regex=False))


# ── _normalize_text ────────────────────────────────────────────────────


def test_normalize_text_lowercases_and_strips_special():
    assert _normalize_text("Monte Carlo!") == "montecarlo"
    assert _normalize_text("VaR 95%") == "var95"
    assert _normalize_text("  Hello-World  ") == "helloworld"


# ── _extract_term_heading ──────────────────────────────────────────────


def test_extract_term_heading_h3():
    assert (
        _extract_term_heading("### Monte Carlo Simulation") == "Monte Carlo Simulation"
    )
    assert _extract_term_heading("### VaR 95%  ") == "VaR 95%"


def test_extract_term_heading_bold():
    assert _extract_term_heading("**Business Value Floor**") == "Business Value Floor"


def test_extract_term_heading_bold_with_colon_returns_none():
    assert _extract_term_heading("**Why this matters:**") is None


def test_extract_term_heading_bold_too_long_returns_none():
    long = "**" + "x" * 101 + "**"
    assert _extract_term_heading(long) is None


def test_extract_term_heading_normal_line_returns_none():
    assert _extract_term_heading("This is a normal paragraph.") is None


# ── _clean_definition ─────────────────────────────────────────────────


def test_clean_definition_joins_lines():
    lines = ["First part.", "  Second part."]
    result = _clean_definition(lines)
    assert "First part." in result
    assert "Second part." in result


def test_clean_definition_skips_blank_lines():
    lines = ["First.", "", "   ", "Second."]
    result = _clean_definition(lines)
    assert "First." in result
    assert "Second." in result


# ── _raw_lines_from_path ──────────────────────────────────────────────


def test_raw_lines_from_md_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("## Section\n### Term\nDefinition text.\n")
        path = Path(f.name)
    try:
        lines = _raw_lines_from_path(path)
        assert any("Section" in line for line in lines)
    finally:
        path.unlink()


# ── _should_skip_glossary_line ────────────────────────────────────────


def test_should_skip_blank():
    assert _should_skip_glossary_line("") is True
    assert _should_skip_glossary_line("---") is True
    assert _should_skip_glossary_line("# Main Header") is True
    assert _should_skip_glossary_line("## Section") is False


# ── _term_matches_tokens ──────────────────────────────────────────────


def test_term_matches_tokens_positive():
    assert _term_matches_tokens("Monte Carlo", ["montecarlo"]) is True


def test_term_matches_tokens_negative():
    assert _term_matches_tokens("Portfolio", ["sharpe"]) is False


# ── _parse_glossary_lines ─────────────────────────────────────────────


def test_parse_glossary_lines_section_handling():
    lines = [
        "## Financial Risk",
        "### VaR 95%",
        "The value at risk at 95% confidence.",
    ]
    rows = _parse_glossary_lines(lines)
    assert any(r["Term"] == "VaR 95%" for r in rows)
    assert any(r["Section"] == "Financial Risk" for r in rows)


def test_parse_glossary_lines_table_rows_skipped():
    lines = [
        "## Section",
        "### Term",
        "| col1 | col2 |",
        "Definition text.",
    ]
    rows = _parse_glossary_lines(lines)
    # Table row should be skipped
    assert any("col1" not in r["Definition"] for r in rows)


# ── load_glossary filters ─────────────────────────────────────────────


def test_load_glossary_section_filter():
    df = load_glossary(include_sections=["Portfolio"])
    assert len(df) > 0
    assert all(df["Section"].str.lower() == "portfolio")


def test_load_glossary_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        load_glossary(glossary_path="/nonexistent/path/glossary.md")


def test_load_glossary_empty_when_no_match():
    df = load_glossary(include_terms=["zzznomatchxxx"])
    assert df.empty


# ── display_glossary ──────────────────────────────────────────────────


def test_display_glossary_returns_dataframe():
    with patch("fhs.notebook.glossary.display", None, create=True):
        df = display_glossary()
    assert not df.empty


def test_display_glossary_empty_filter(capsys):
    display_glossary(include_terms=["zzznomatchyyy"])
    captured = capsys.readouterr()
    assert "No glossary entries" in captured.out


# ── glossary_widget ───────────────────────────────────────────────────


def test_glossary_widget_without_ipywidgets_falls_back():
    with patch.dict("sys.modules", {"ipywidgets": None}):
        result = glossary_widget()
    assert result is None


def test_glossary_widget_empty_filter_returns_none(capsys):
    with patch.dict("sys.modules", {"ipywidgets": None}):
        result = glossary_widget(include_sections=["ZZZNoMatchSection"])
    assert result is None

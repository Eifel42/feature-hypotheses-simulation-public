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

"""Tests for interactive Plotly chart functions."""

from __future__ import annotations

import numpy as np

from fhs.presentation.notebook.charts.interactive import (
    plot_feature_distributions_interactive,
    plot_multi_year_fan_interactive,
    plot_risk_profile_interactive,
)

# ── Minimal stubs ─────────────────────────────────────────────────────────────


class _FakeResult:
    def __init__(self, name="Feature A", n=500, seed=0):
        rng = np.random.default_rng(seed)
        self.feature_name = name
        self.results_array = rng.normal(50_000, 10_000, n)
        self.expected_value = float(self.results_array.mean())
        self.var_95 = float(np.percentile(self.results_array, 5))
        self.p95 = float(np.percentile(self.results_array, 95))


class _FakeYearResult:
    def __init__(self, year, expected, var_95, p95):
        self.year = year
        self.expected = expected
        self.var_95 = var_95
        self.p95 = p95


class _FakeMultiYearResult:
    def __init__(self, name="Feature A"):
        self.feature_name = name
        self.years = [
            _FakeYearResult(1, 50_000, 30_000, 70_000),
            _FakeYearResult(2, 55_000, 33_000, 77_000),
            _FakeYearResult(3, 60_000, 36_000, 84_000),
        ]


class _FakeFeature:
    annual_installment = 10_000.0
    installment_years = 2


# ── plot_risk_profile_interactive ─────────────────────────────────────────────


def test_risk_profile_interactive_returns_figure():
    result = _FakeResult()
    fig = plot_risk_profile_interactive(result)
    # Plotly figures have a `data` attribute
    assert hasattr(fig, "data")
    assert len(fig.data) > 0


def test_risk_profile_interactive_has_histogram_trace():
    import plotly.graph_objects as go

    result = _FakeResult()
    fig = plot_risk_profile_interactive(result)
    histograms = [t for t in fig.data if isinstance(t, go.Histogram)]
    assert len(histograms) == 1


def test_risk_profile_interactive_uses_feature_name_in_title():
    result = _FakeResult(name="Special Feature")
    fig = plot_risk_profile_interactive(result)
    assert "Special Feature" in fig.layout.title.text


def test_risk_profile_interactive_uses_decision_labels():
    result = _FakeResult()
    fig = plot_risk_profile_interactive(result)
    assert "Decision Profile" in fig.layout.title.text
    metric_labels = list(fig.data[1].cells.values[0])
    assert "Business Value Floor 95" in metric_labels


def test_risk_profile_interactive_missing_feature_name_defaults():
    result = _FakeResult()
    del result.feature_name  # remove the attribute
    fig = plot_risk_profile_interactive(result)
    assert fig is not None


# ── plot_feature_distributions_interactive ────────────────────────────────────


def test_feature_distributions_interactive_single():
    results = [_FakeResult("F1")]
    fig = plot_feature_distributions_interactive(results)
    assert hasattr(fig, "data")
    assert len(fig.data) == 1


def test_feature_distributions_interactive_multiple():
    results = [_FakeResult(f"F{i}", seed=i) for i in range(3)]
    fig = plot_feature_distributions_interactive(results)
    # One histogram per feature
    import plotly.graph_objects as go

    histograms = [t for t in fig.data if isinstance(t, go.Histogram)]
    assert len(histograms) == 3


def test_feature_distributions_interactive_custom_title():
    results = [_FakeResult()]
    fig = plot_feature_distributions_interactive(results, title="My Distribution")
    assert "My Distribution" in fig.layout.title.text


def test_feature_distributions_interactive_custom_colors():
    from fhs.presentation.notebook.styling import palette

    results = [_FakeResult("F1"), _FakeResult("F2")]
    colors = [palette["danger"], palette["accent"]]
    fig = plot_feature_distributions_interactive(results, colors=colors)
    assert len(fig.data) == 2


# ── plot_multi_year_fan_interactive ───────────────────────────────────────────


def test_multi_year_fan_interactive_single_feature():
    myr = [_FakeMultiYearResult("F1")]
    fig = plot_multi_year_fan_interactive(myr)
    assert hasattr(fig, "data")
    assert len(fig.data) > 0


def test_multi_year_fan_interactive_multiple_features():
    myr = [_FakeMultiYearResult(f"F{i}") for i in range(3)]
    fig = plot_multi_year_fan_interactive(myr)
    # Each feature: band + floor + expected + ceiling = 4 traces
    assert len(fig.data) >= 3 * 4


def test_multi_year_fan_interactive_with_features_overlay():
    myr = [_FakeMultiYearResult("F1")]
    features = [_FakeFeature()]
    fig = plot_multi_year_fan_interactive(myr, features=features)
    # Should add installment trace on top of the 4 standard traces
    assert len(fig.data) >= 5


def test_multi_year_fan_interactive_custom_title():
    myr = [_FakeMultiYearResult()]
    fig = plot_multi_year_fan_interactive(myr, title="5-Year Outlook")
    assert "5-Year Outlook" in fig.layout.title.text


def test_multi_year_fan_interactive_uses_business_value_floor_trace_name():
    myr = [_FakeMultiYearResult("F1")]
    fig = plot_multi_year_fan_interactive(myr)
    trace_names = [trace.name for trace in fig.data]
    assert "Business Value Floor 95" in trace_names


def test_multi_year_fan_interactive_no_installment_when_zero():
    myr = [_FakeMultiYearResult("F1")]

    class _ZeroInstallment:
        annual_installment = 0.0
        installment_years = 1

    fig_without = plot_multi_year_fan_interactive(myr, features=[_ZeroInstallment()])
    fig_plain = plot_multi_year_fan_interactive(myr)
    # No extra installment trace when installment is 0
    assert len(fig_without.data) == len(fig_plain.data)


# ── Public API export ─────────────────────────────────────────────────────────


def test_interactive_functions_exported_from_charts_package():
    from fhs.presentation.notebook import charts

    assert hasattr(charts, "plot_risk_profile_interactive")
    assert hasattr(charts, "plot_feature_distributions_interactive")
    assert hasattr(charts, "plot_multi_year_fan_interactive")


def test_interactive_functions_exported_from_presentation_notebook():
    import fhs.presentation.notebook as nb

    assert hasattr(nb, "plot_risk_profile_interactive")
    assert hasattr(nb, "plot_feature_distributions_interactive")
    assert hasattr(nb, "plot_multi_year_fan_interactive")

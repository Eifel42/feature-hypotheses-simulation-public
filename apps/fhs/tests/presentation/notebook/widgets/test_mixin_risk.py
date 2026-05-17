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

"""Tests for _RiskMixin display methods."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")

from fhs.presentation.notebook.widgets.facade import FHSDisplay


class _RecorderDisplay(FHSDisplay):
    def __init__(self) -> None:
        self.rendered: list[str] = []

    def __call__(self, html: str) -> None:
        self.rendered.append(html)


# ── downside_risk ─────────────────────────────────────────────────────


class TestDownsideRisk:
    def test_calls_self_with_html(self):
        display = _RecorderDisplay()
        result = SimpleNamespace(
            var_95=50_000.0, cvar_95=70_000.0, expected_value=200_000.0
        )
        display.downside_risk(result)
        assert len(display.rendered) == 1
        assert isinstance(display.rendered[0], str)

    def test_custom_title_is_passed(self):
        display = _RecorderDisplay()
        result = SimpleNamespace(
            var_95=50_000.0, cvar_95=70_000.0, expected_value=200_000.0
        )
        display.downside_risk(result, title="Custom Title")
        assert len(display.rendered) == 1


# ── feature_risk_layer_decay ──────────────────────────────────────────


class TestFeatureRiskLayerDecay:
    def test_calls_chart_function(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_layer_decay"
        ) as mock_plot:
            display.feature_risk_layer_decay(
                ["F1", "F2"],
                [[100_000.0, 80_000.0], [90_000.0, 70_000.0]],
            )
        mock_plot.assert_called_once()

    def test_with_explicit_labels(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_layer_decay"
        ) as mock_plot:
            display.feature_risk_layer_decay(
                ["F1"],
                [[100_000.0, 80_000.0]],
                layer_labels=["Base", "Delivery"],
                title="Custom Decay Title",
            )
        mock_plot.assert_called_once()


# ── executive_risk_summary ────────────────────────────────────────────


class TestExecutiveRiskSummary:
    def test_profitable_scenario(self):
        display = _RecorderDisplay()
        display.executive_risk_summary(
            before=1_000_000.0,
            after=800_000.0,
            investment=500_000.0,
            dominant_risk="Delivery",
        )
        assert len(display.rendered) == 1
        html = display.rendered[0]
        assert "EUR 1,000,000" in html
        assert "EUR 800,000" in html
        assert "profitable" in html.lower()

    def test_unprofitable_scenario(self):
        display = _RecorderDisplay()
        display.executive_risk_summary(
            before=500_000.0,
            after=300_000.0,
            investment=400_000.0,
            dominant_risk="Market",
        )
        html = display.rendered[0]
        assert "NOT profitable" in html

    def test_with_profitability_pct(self):
        display = _RecorderDisplay()
        display.executive_risk_summary(
            before=1_000_000.0,
            after=900_000.0,
            investment=400_000.0,
            dominant_risk="Delivery",
            profitability_pct=0.75,
        )
        html = display.rendered[0]
        assert "75%" in html

    def test_zero_before_does_not_crash(self):
        display = _RecorderDisplay()
        display.executive_risk_summary(
            before=0.0,
            after=0.0,
            investment=100_000.0,
            dominant_risk="Market",
        )
        assert len(display.rendered) == 1


# ── risk_register_table ───────────────────────────────────────────────


class TestRiskRegisterTable:
    def test_renders_rows(self):
        display = _RecorderDisplay()
        rows = [
            ("Delivery", "10%", "Total loss", "EUR 100,000", "HIGH", "Reduce LLP"),
        ]
        display.risk_register_table(rows)
        assert len(display.rendered) == 1

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.risk_register_table([], title="My Register")
        assert len(display.rendered) == 1


# ── portfolio_feature_cards ───────────────────────────────────────────


class TestPortfolioFeatureCards:
    @staticmethod
    def _make_card(retention_pct: float) -> dict:
        return {
            "name": "Feature A",
            "investment": 100_000.0,
            "base_bv": 300_000.0,
            "final_bv": 300_000.0 * retention_pct / 100,
            "retention_pct": retention_pct,
            "biggest_risk": "Delivery (EUR 50,000 lost)",
            "action": "Accept",
        }

    def test_green_retention(self):
        display = _RecorderDisplay()
        display.portfolio_feature_cards([self._make_card(75.0)])
        html = display.rendered[0]
        assert "GREEN" in html

    def test_yellow_retention(self):
        display = _RecorderDisplay()
        display.portfolio_feature_cards([self._make_card(45.0)])
        html = display.rendered[0]
        assert "YELLOW" in html

    def test_red_retention(self):
        display = _RecorderDisplay()
        display.portfolio_feature_cards([self._make_card(20.0)])
        html = display.rendered[0]
        assert "RED" in html

    def test_empty_card_data(self):
        display = _RecorderDisplay()
        display.portfolio_feature_cards([])
        assert len(display.rendered) == 1

    def test_multiple_cards(self):
        display = _RecorderDisplay()
        display.portfolio_feature_cards(
            [
                self._make_card(80.0),
                self._make_card(40.0),
                self._make_card(10.0),
            ]
        )
        html = display.rendered[0]
        assert "GREEN" in html
        assert "YELLOW" in html
        assert "RED" in html


# ── combined_sensitivity_table ────────────────────────────────────────


class TestCombinedSensitivityTable:
    @staticmethod
    def _make_result(expected: float) -> object:
        return SimpleNamespace(after_risk_3=SimpleNamespace(expected=expected))

    def test_renders_two_rows(self):
        display = _RecorderDisplay()
        r2_results = {
            0.10: self._make_result(900_000.0),
            0.20: self._make_result(800_000.0),
            0.30: self._make_result(700_000.0),
        }
        r3_results = {
            0.025: self._make_result(950_000.0),
            0.05: self._make_result(850_000.0),
            0.075: self._make_result(750_000.0),
        }
        display.combined_sensitivity_table(
            r2_results, r3_results, [0.10, 0.20, 0.30], [0.025, 0.05, 0.075]
        )
        assert len(display.rendered) == 1

    def test_custom_title(self):
        display = _RecorderDisplay()
        r2 = {0.10: self._make_result(1_000_000.0), 0.20: self._make_result(900_000.0)}
        r3 = {0.025: self._make_result(1_000_000.0), 0.05: self._make_result(950_000.0)}
        display.combined_sensitivity_table(
            r2, r3, [0.10, 0.20], [0.025, 0.05], title="Sensitivity"
        )
        assert len(display.rendered) == 1


# ── feature_risk_decay (static) ───────────────────────────────────────


class TestFeatureRiskDecay:
    def test_calls_chart_function(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_decay"
        ) as mock_plot:
            display.feature_risk_decay(
                ["F1", "F2"],
                [[100.0, 80.0, 60.0], [90.0, 70.0, 50.0]],
            )
        mock_plot.assert_called_once()

    def test_with_labels_and_title(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_decay"
        ) as mock_plot:
            display.feature_risk_decay(
                ["F1"],
                [[100.0, 70.0]],
                layer_labels=["Base", "Final"],
                title="Decay Chart",
            )
        mock_plot.assert_called_once()


# ── feature_risk_profile_cards ────────────────────────────────────────


class TestFeatureRiskProfileCards:
    @staticmethod
    def _make_feature(name: str, cost: float) -> object:
        return SimpleNamespace(name=name, development_cost=cost)

    @staticmethod
    def _make_profile(base_exp: float, final_exp: float) -> object:
        mid = (base_exp + final_exp) / 2
        return SimpleNamespace(
            base=SimpleNamespace(expected=base_exp),
            after_risk_1=SimpleNamespace(expected=base_exp * 0.95),
            after_risk_2=SimpleNamespace(expected=mid + (base_exp - mid) * 0.5),
            after_component=SimpleNamespace(expected=mid),
            after_risk_3=SimpleNamespace(expected=final_exp),
        )

    def test_renders_cards(self):
        display = _RecorderDisplay()
        features = [self._make_feature("H1: Feature A", 100_000.0)]
        profiles = {"H1: Feature A": self._make_profile(500_000.0, 350_000.0)}
        display.feature_risk_profile_cards(features, profiles)
        assert len(display.rendered) == 1

    def test_missing_profile_skipped(self):
        display = _RecorderDisplay()
        features = [self._make_feature("H1: Feature A", 100_000.0)]
        display.feature_risk_profile_cards(features, {})
        # renders empty container
        assert len(display.rendered) == 1
        assert display.rendered[0].count("<div") >= 1

    def test_high_risk_feature(self):
        display = _RecorderDisplay()
        features = [self._make_feature("F1", 100_000.0)]
        profiles = {"F1": self._make_profile(500_000.0, 100_000.0)}
        display.feature_risk_profile_cards(features, profiles)
        html = display.rendered[0]
        assert "RED" in html

    def test_low_risk_feature(self):
        display = _RecorderDisplay()
        features = [self._make_feature("F1", 100_000.0)]
        profiles = {"F1": self._make_profile(500_000.0, 460_000.0)}
        display.feature_risk_profile_cards(features, profiles)
        html = display.rendered[0]
        assert "GREEN" in html


# ── feature_risk_decay_from_profiles ─────────────────────────────────


class TestFeatureRiskDecayFromProfiles:
    @staticmethod
    def _make_profile() -> object:
        return SimpleNamespace(
            base=SimpleNamespace(expected=500_000.0),
            after_risk_1=SimpleNamespace(expected=470_000.0),
            after_risk_2=SimpleNamespace(expected=450_000.0),
            after_component=SimpleNamespace(expected=430_000.0),
            after_risk_3=SimpleNamespace(expected=400_000.0),
        )

    def test_calls_decay_chart(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_decay"
        ) as mock_plot:
            profiles = {"F1": self._make_profile(), "F2": self._make_profile()}
            display.feature_risk_decay_from_profiles(["F1", "F2"], profiles)
        mock_plot.assert_called_once()

    def test_with_custom_labels(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_decay"
        ) as mock_plot:
            profiles = {"F1": self._make_profile()}
            display.feature_risk_decay_from_profiles(
                ["F1"],
                profiles,
                layer_labels=["Base", "D", "M", "C", "G"],
                title="Custom Decay",
            )
        mock_plot.assert_called_once()

    def test_strips_feature_name_prefix(self):
        display = _RecorderDisplay()
        with patch(
            "fhs.presentation.notebook.charts.risk.plot_feature_risk_decay"
        ) as mock_plot:
            profiles = {"H1: Feature A": self._make_profile()}
            display.feature_risk_decay_from_profiles(["H1: Feature A"], profiles)
        args = mock_plot.call_args[0]
        assert args[0] == ["Feature A"]

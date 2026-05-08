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
Tests for the plotting/simulation module.

Covers plot_results, _plot_results_plotly, and plot_comparison.
"""

from unittest.mock import patch

import numpy as np

from fhs.core.model import Feature, SimulationResult


class TestPlottingSimulationCoverage:
    """Cover uncovered plotting paths in simulation.py."""

    @staticmethod
    def _make_result():
        rng = np.random.default_rng(0)
        return SimulationResult(
            feature_name="PlotTest",
            results=rng.normal(150, 15, 2000),
            scenarios=2000,
            expected_value=150,
        )

    @patch("fhs.plotting.simulation.go", create=True)
    def test_plot_results_interactive(self, _mock_go):
        """interactive=True triggers _plot_results_plotly."""
        from fhs.plotting import simulation as sim_mod

        result = self._make_result()
        risk = {"var_95": 120.0, "var_99": 110.0}

        with patch.object(sim_mod, "_plot_results_plotly") as mock_plotly:
            sim_mod.plot_results(result, risk_analysis=risk, interactive=True)
            mock_plotly.assert_called_once()

    def test_plot_results_plotly_full(self):
        """_plot_results_plotly full execution."""
        from fhs.plotting.simulation import _plot_results_plotly

        result = self._make_result()
        risk = {"var_95": 120.0, "var_99": 110.0, "confidence_interval": [100.0, 200.0]}

        with patch("plotly.graph_objects.Figure.show"):
            _plot_results_plotly(result, risk)

    def test_plot_results_plotly_no_risk(self):
        """_plot_results_plotly without risk analysis."""
        from fhs.plotting.simulation import _plot_results_plotly

        result = self._make_result()
        with patch("plotly.graph_objects.Figure.show"):
            _plot_results_plotly(result, None)

    @patch("matplotlib.pyplot.show")
    def test_plot_comparison_list_format(self, mock_show):
        """plot_comparison with list input (not dict)."""
        from fhs.plotting.simulation import plot_comparison

        rng = np.random.default_rng(0)
        feature_a = Feature(
            name="A", expected_users=500, conversion_rate=0.3, uncertainty=0.1
        )
        feature_b = Feature(
            name="B", expected_users=800, conversion_rate=0.2, uncertainty=0.15
        )
        r1 = SimulationResult("A", rng.normal(150, 10, 1000), 1000, expected_value=150)
        r2 = SimulationResult("B", rng.normal(160, 12, 1000), 1000, expected_value=160)

        comparison_list = [
            {
                "feature": feature_a,
                "simulation": r1,
                "risk": {"mean": 150.0, "var_95": 130.0},
            },
            {
                "feature": feature_b,
                "simulation": r2,
                "risk": {"mean": 160.0, "var_95": 135.0},
            },
        ]
        plot_comparison(comparison_list)
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_plot_comparison_empty(self, mock_show):
        """plot_comparison with empty comparison."""
        from fhs.plotting.simulation import plot_comparison

        plot_comparison(None)
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_plot_comparison_dict_format(self, mock_show):
        """plot_comparison with dict format."""
        from fhs.plotting.simulation import plot_comparison

        rng = np.random.default_rng(0)
        r1 = SimulationResult("P", rng.normal(100, 10, 1000), 1000, expected_value=100)
        comparison_dict = {
            "Premium": {
                "simulation_result": r1,
                "risk_analysis": {"mean": 100.0, "var_95": 80.0},
            }
        }
        plot_comparison(comparison_dict)
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_plot_comparison_no_var95_in_risk(self, mock_show):
        """plot_comparison fallback when risk_analysis has no 'var_95'."""
        from fhs.plotting.simulation import plot_comparison

        rng = np.random.default_rng(0)
        r1 = SimulationResult("X", rng.normal(100, 10, 1000), 1000, expected_value=100)
        comparison_dict = {
            "FeatureX": {
                "simulation_result": r1,
                "risk_analysis": {"mean": 100.0},  # no var_95 key
            }
        }
        plot_comparison(comparison_dict)
        mock_show.assert_called_once()

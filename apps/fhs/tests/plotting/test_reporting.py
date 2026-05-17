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
Tests for the plotting/reporting module.

Covers all Reporter static methods including portfolio summaries,
confidence intervals, feature comparisons, and executive dashboards.
"""

import numpy as np
import pandas as pd

from fhs.core.model import SimulationResult
from fhs.plotting.reporting import Reporter


class TestReportingCoverage:
    """Cover all Reporter static methods in plotting/reporting.py."""

    @staticmethod
    def _make_portfolio_risk():
        """Helper: build portfolio_risk VO."""
        from fhs.core.model import (
            DiversificationMetrics,
            IndividualRiskMetrics,
            PortfolioMetrics,
            PortfolioRiskResult,
        )

        return PortfolioRiskResult(
            portfolio_metrics=PortfolioMetrics(
                expected_value=50000,
                var_95=30000,
                var_99=20000,
                cvar_95=25000,
                cvar_99=22000,
                std_dev=10000,
            ),
            individual_risks={
                "Premium": IndividualRiskMetrics(
                    var_95=18000, cvar_95=15000, mean=30000, std=6000
                ),
                "Basic": IndividualRiskMetrics(
                    var_95=12000, cvar_95=10000, mean=20000, std=4000
                ),
            },
            diversification=DiversificationMetrics(
                weighted_individual_var=35000,
                portfolio_var=30000,
                diversification_benefit=5000,
                diversification_ratio=0.15,
            ),
            weights={"Premium": 0.6, "Basic": 0.4},
            n_features=2,
        )

    @staticmethod
    def _make_sim_results():
        """Helper: two SimulationResults for reporting."""
        rng = np.random.default_rng(0)
        r1 = SimulationResult(
            feature_name="Premium",
            results=rng.normal(300, 30, 2000),
            scenarios=2000,
            expected_value=300,
        )
        r2 = SimulationResult(
            feature_name="Basic",
            results=rng.normal(200, 20, 2000),
            scenarios=2000,
            expected_value=200,
        )
        return {"Premium": r1, "Basic": r2}

    def test_get_portfolio_summary(self):
        """get_portfolio_summary returns DataFrame."""
        df = Reporter.get_portfolio_summary(self._make_portfolio_risk())
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 7

    def test_get_confidence_interval_summary(self):
        """get_confidence_interval_summary."""
        data = np.random.default_rng(0).normal(100, 10, 1000)
        ci = Reporter.get_confidence_interval_summary(data)
        assert "mean" in ci
        assert ci["lower"] < ci["upper"]
        assert ci["confidence"] == 0.95

    def test_get_feature_comparison_table(self):
        """get_feature_comparison_table."""
        df = Reporter.get_feature_comparison_table(self._make_sim_results())
        assert isinstance(df, pd.DataFrame)
        assert "Feature" in df.columns
        assert len(df) == 2

    def test_plot_risk_distributions(self):
        """plot_risk_distributions."""
        fig = Reporter.plot_risk_distributions(self._make_sim_results())
        assert fig is not None

    def test_format_feature_assessment(self):
        """format_feature_assessment."""
        assessment = {
            "feature": "Premium",
            "expected_business_value": 50000,
            "var_95_business_value": 30000,
            "opportunity_cost": 50000,
            "downside_risk": 20000,
            "risk_ratio": 0.4,
            "confidence_interval": [25000, 55000],
            "recommendation": "Medium risk",
        }
        text = Reporter.format_feature_assessment(assessment)
        assert "Premium" in text
        assert "Expected Business Value" in text

    def test_format_portfolio_recommendation(self):
        """format_portfolio_recommendation."""
        optimization = {
            "recommended_features": ["Premium", "Basic"],
            "max_features": 2,
            "total_expected_business_value": 90000,
            "portfolio_var_95": 50000,
            "portfolio_risk_ratio": 0.3,
            "excluded_features": [
                {"name": "Risky", "reason": "High risk ratio"},
            ],
            "alternatives": [
                {
                    "features": ["Premium", "Risky"],
                    "expected_business_value": 80000,
                    "var_95_business_value": 40000,
                },
            ],
        }
        text = Reporter.format_portfolio_recommendation(optimization)
        assert "Premium" in text
        assert "Excluded" in text
        assert "Alternatives" in text

    def test_format_portfolio_recommendation_no_alternatives(self):
        """format_portfolio_recommendation without alternatives."""
        optimization = {
            "recommended_features": ["Premium"],
            "max_features": 1,
            "total_expected_business_value": 50000,
            "portfolio_var_95": 30000,
            "portfolio_risk_ratio": 0.2,
            "excluded_features": [],
            "alternatives": [],
        }
        text = Reporter.format_portfolio_recommendation(optimization)
        assert "Premium" in text

    def test_plot_portfolio_optimization(self):
        """plot_portfolio_optimization returns figure."""
        optimization = {
            "recommended_features": ["Premium", "Basic"],
            "total_expected_business_value": 90000,
            "portfolio_var_95": 50000,
            "alternatives": [
                {
                    "features": ["Premium", "Risky"],
                    "expected_business_value": 80000,
                    "var_95_business_value": 40000,
                },
                {
                    "features": ["Basic", "Risky"],
                    "expected_business_value": 70000,
                    "var_95_business_value": 35000,
                },
            ],
        }
        fig = Reporter.plot_portfolio_optimization(optimization)
        assert fig is not None

    def test_plot_portfolio_optimization_no_alternatives(self):
        """plot_portfolio_optimization with no alternatives returns None."""
        optimization = {
            "recommended_features": ["Premium"],
            "alternatives": [],
        }
        result = Reporter.plot_portfolio_optimization(optimization)
        assert result is None

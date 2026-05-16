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

"""Tests for sprint delivery value objects."""

from __future__ import annotations

import numpy as np

from fhs.core.model.value_objects.sprint_delivery import (
    DeliverySimulationResult,
    PortfolioProfitabilityResult,
    ProfitabilityResult,
)


def test_delivery_simulation_result_cost_uplift_zero_sprints():
    """Test cost_uplift when planned_sprints is zero."""
    result = DeliverySimulationResult(
        feature_name="Feature A",
        planned_sprints=0,
        actual_sprints=np.array([5, 6]),
        business_value_after_risk=np.array([150_000.0, 160_000.0]),
        actual_cost=np.array([120_000.0, 130_000.0]),
        cancelled=np.array([False, False]),
    )
    assert result.cost_uplift == 0.0


def test_profitability_result_break_even_probability_empty():
    """Test break_even_probability with empty distribution."""
    result = ProfitabilityResult(
        feature_name="Feature A",
        profit_distribution=np.array([]),
        planned_cost=100_000.0,
        expected_business_value=150_000.0,
        expected_cost=110_000.0,
    )
    assert result.break_even_probability == 0.0


def test_profitability_result_expected_loss_no_losses():
    """Test expected_loss when there are no losses."""
    result = ProfitabilityResult(
        feature_name="Feature A",
        profit_distribution=np.array([10_000.0, 20_000.0, 30_000.0]),
        planned_cost=100_000.0,
        expected_business_value=150_000.0,
        expected_cost=110_000.0,
    )
    assert result.expected_loss == 0.0


def test_profitability_result_loss_at_risk_empty():
    """Test loss_at_risk_95 with empty distribution."""
    result = ProfitabilityResult(
        feature_name="Feature A",
        profit_distribution=np.array([]),
        planned_cost=100_000.0,
        expected_business_value=150_000.0,
        expected_cost=110_000.0,
    )
    assert result.loss_at_risk_95 == 0.0


def test_profitability_result_profit_margin_zero_cost():
    """Test profit_margin when expected_cost is zero."""
    result = ProfitabilityResult(
        feature_name="Feature A",
        profit_distribution=np.array([10_000.0, 20_000.0]),
        planned_cost=100_000.0,
        expected_business_value=150_000.0,
        expected_cost=0.0,
    )
    assert result.profit_margin == 0.0


def test_portfolio_profitability_result_break_even_empty():
    """Test portfolio_break_even_probability with empty distribution."""
    result = PortfolioProfitabilityResult(
        feature_results=(),
        portfolio_profit=np.array([]),
        total_investment=500_000.0,
    )
    assert result.portfolio_break_even_probability == 0.0


def test_portfolio_profitability_result_loss_at_risk_empty():
    """Test portfolio_loss_at_risk_95 with empty distribution."""
    result = PortfolioProfitabilityResult(
        feature_results=(),
        portfolio_profit=np.array([]),
        total_investment=500_000.0,
    )
    assert result.portfolio_loss_at_risk_95 == 0.0


def test_portfolio_profitability_result_profit_p5_empty():
    """Test portfolio_profit_p5 with empty distribution."""
    result = PortfolioProfitabilityResult(
        feature_results=(),
        portfolio_profit=np.array([]),
        total_investment=500_000.0,
    )
    assert result.portfolio_profit_p5 == 0.0


def test_portfolio_profitability_result_expected_loss_no_losses():
    """Test portfolio_expected_loss when there are no losses."""
    result = PortfolioProfitabilityResult(
        feature_results=(),
        portfolio_profit=np.array([10_000.0, 20_000.0, 30_000.0]),
        total_investment=500_000.0,
    )
    assert result.portfolio_expected_loss == 0.0


def test_portfolio_profitability_result_expected_loss_with_losses():
    """Test portfolio_expected_loss when there are losses."""

    from fhs.core.model.value_objects.sprint_delivery import (
        PortfolioProfitabilityResult,
    )

    # Mix of profits and losses
    result = PortfolioProfitabilityResult(
        feature_results=(),
        portfolio_profit=np.array([10_000.0, -5_000.0, -10_000.0, 20_000.0]),
        total_investment=500_000.0,
    )
    # Should calculate average of negative values
    assert result.portfolio_expected_loss > 0.0

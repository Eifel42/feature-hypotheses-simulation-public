#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Tests for Value Objects."""

import numpy as np
import pytest
from pydantic import ValidationError

from fhs.core.model.exceptions import ValidationError as DomainValidationError
from fhs.core.model.value_objects import (
    BetaParameters,
    Budget,
    ConfidenceLevel,
    OptimizationStrategy,
    RiskMetric,
    YearResult,
)


class TestBudget:
    """Tests for Budget Value Object."""

    def test_budget_creation(self):
        """Test creating a budget."""
        budget = Budget(amount=100_000.0, currency="EUR")
        assert budget.amount == 100_000.0
        assert budget.currency == "EUR"

    def test_budget_default_currency(self):
        """Test default currency is EUR."""
        budget = Budget(amount=50_000.0)
        assert budget.currency == "EUR"

    def test_budget_negative_amount_raises(self):
        """Test negative budget raises validation error."""
        with pytest.raises(ValidationError):
            Budget(amount=-1000.0)

    def test_budget_addition(self):
        """Test adding two budgets."""
        b1 = Budget(amount=50_000.0, currency="EUR")
        b2 = Budget(amount=30_000.0, currency="EUR")
        result = b1 + b2
        assert result.amount == 80_000.0
        assert result.currency == "EUR"

    def test_budget_subtraction(self):
        """Test subtracting two budgets."""
        b1 = Budget(amount=50_000.0, currency="EUR")
        b2 = Budget(amount=30_000.0, currency="EUR")
        result = b1 - b2
        assert result.amount == 20_000.0
        assert result.currency == "EUR"

    def test_budget_addition_different_currencies_raises(self):
        """Test adding budgets with different currencies raises error."""
        b1 = Budget(amount=50_000.0, currency="EUR")
        b2 = Budget(amount=30_000.0, currency="USD")
        with pytest.raises(ValueError, match="different currencies"):
            _ = b1 + b2

    def test_budget_comparison(self):
        """Test comparing budgets."""
        b1 = Budget(amount=50_000.0, currency="EUR")
        b2 = Budget(amount=30_000.0, currency="EUR")
        assert b2 < b1
        assert b2 <= b1
        assert not (b1 < b2)

    def test_budget_comparison_different_currencies_raises(self):
        """Test comparing budgets with different currencies raises error."""
        b1 = Budget(amount=50_000.0, currency="EUR")
        b2 = Budget(amount=30_000.0, currency="USD")
        with pytest.raises(ValueError, match="different currencies"):
            _ = b1 < b2

    def test_budget_str(self):
        """Test string representation."""
        budget = Budget(amount=100_000.0, currency="EUR")
        assert str(budget) == "100,000.00 EUR"


class TestRiskMetric:
    """Tests for RiskMetric Value Object."""

    def test_risk_metric_creation(self):
        """Test creating a risk metric."""
        metric = RiskMetric(var=50_000.0, cvar=45_000.0, confidence_level=0.95)
        assert metric.var == 50_000.0
        assert metric.cvar == 45_000.0
        assert metric.confidence_level == 0.95

    def test_risk_metric_default_confidence_level(self):
        """Test default confidence level is 0.95."""
        metric = RiskMetric(var=50_000.0, cvar=45_000.0)
        assert metric.confidence_level == 0.95

    def test_cvar_must_be_less_than_or_equal_to_var(self):
        """Test CVaR must be <= VaR."""
        # Valid: CVaR < VaR
        metric = RiskMetric(var=50_000.0, cvar=45_000.0)
        assert metric.cvar < metric.var

        # Valid: CVaR == VaR
        metric = RiskMetric(var=50_000.0, cvar=50_000.0)
        assert metric.cvar == metric.var

        # Invalid: CVaR > VaR
        with pytest.raises(ValidationError, match="CVaR.*must be <= VaR"):
            RiskMetric(var=50_000.0, cvar=55_000.0)

    def test_is_acceptable(self):
        """Test is_acceptable method."""
        metric = RiskMetric(var=50_000.0, cvar=45_000.0)
        assert metric.is_acceptable(40_000.0) is True
        assert metric.is_acceptable(60_000.0) is False

    def test_risk_metric_str(self):
        """Test string representation."""
        metric = RiskMetric(var=50_000.0, cvar=45_000.0, confidence_level=0.95)
        assert str(metric) == "VaR95=50,000, CVaR95=45,000"


class TestOptimizationStrategy:
    """Tests for OptimizationStrategy Enum."""

    def test_optimization_strategy_values(self):
        """Test all strategy values."""
        assert OptimizationStrategy.VAR_FLOOR.value == "var_floor"
        assert OptimizationStrategy.EXPECTED.value == "expected"
        assert OptimizationStrategy.SHARPE.value == "sharpe"
        assert OptimizationStrategy.NPV_YEAR1.value == "npv_year1"
        assert OptimizationStrategy.NPV_3YEAR.value == "npv_3year"

    def test_optimization_strategy_str(self):
        """Test string representation."""
        assert str(OptimizationStrategy.VAR_FLOOR) == "var_floor"
        assert str(OptimizationStrategy.EXPECTED) == "expected"
        assert str(OptimizationStrategy.SHARPE) == "sharpe"
        assert str(OptimizationStrategy.NPV_YEAR1) == "npv_year1"
        assert str(OptimizationStrategy.NPV_3YEAR) == "npv_3year"

    def test_optimization_strategy_comparison(self):
        """Test strategy comparison."""
        assert OptimizationStrategy.VAR_FLOOR == OptimizationStrategy.VAR_FLOOR
        assert OptimizationStrategy.VAR_FLOOR != OptimizationStrategy.EXPECTED


class TestConfidenceLevel:
    """Tests for ConfidenceLevel Value Object."""

    def test_confidence_level_creation(self):
        """Test creating a confidence level."""
        cl = ConfidenceLevel(level=0.95)
        assert cl.level == 0.95

    def test_confidence_level_from_percentage(self):
        """Test creating from percentage."""
        cl = ConfidenceLevel.from_percentage(95)
        assert cl.level == 0.95

    def test_confidence_level_to_percentage(self):
        """Test converting to percentage."""
        cl = ConfidenceLevel(level=0.95)
        assert cl.to_percentage() == 95.0

    def test_confidence_level_invalid_range(self):
        """Test confidence level must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ConfidenceLevel(level=1.5)
        with pytest.raises(ValidationError):
            ConfidenceLevel(level=-0.1)

    def test_confidence_level_str(self):
        """Test string representation."""
        cl = ConfidenceLevel(level=0.95)
        assert str(cl) == "95.0%"


class TestBetaParameters:
    """Tests for BetaParameters Value Object."""

    def test_from_mean_uncertainty_typical(self):
        params = BetaParameters.from_mean_uncertainty(mean=0.5, uncertainty=0.3)
        assert params.alpha > 0
        assert params.beta > 0

    def test_from_mean_uncertainty_near_bounds(self):
        low = BetaParameters.from_mean_uncertainty(mean=0.01, uncertainty=0.5)
        high = BetaParameters.from_mean_uncertainty(mean=0.99, uncertainty=0.5)
        assert low.alpha > 0
        assert low.beta > 0
        assert high.alpha > 0
        assert high.beta > 0

    def test_from_mean_uncertainty_invalid_mean(self):
        with pytest.raises(DomainValidationError, match="Beta distribution"):
            BetaParameters.from_mean_uncertainty(mean=0.0, uncertainty=0.3)


def test_year_result_from_scenarios() -> None:
    scenarios = np.array([100.0, 200.0, 300.0, 400.0, 500.0], dtype=float)

    result = YearResult.from_scenarios(year=1, scenarios=scenarios)

    assert result.year == 1
    assert result.expected == pytest.approx(300.0)
    assert result.var_95 == pytest.approx(np.percentile(scenarios, 5))
    assert result.p95 == pytest.approx(np.percentile(scenarios, 95))
    assert result.std == pytest.approx(float(np.std(scenarios)))


@pytest.mark.parametrize(
    "obj,attr",
    [
        (Budget(amount=100_000.0), "amount"),
        (RiskMetric(var=50_000.0, cvar=45_000.0), "var"),
        (ConfidenceLevel(level=0.95), "level"),
    ],
    ids=["Budget", "RiskMetric", "ConfidenceLevel"],
)
def test_value_objects_are_immutable(obj, attr):
    """All value objects must be frozen (immutable)."""
    with pytest.raises(ValidationError):
        setattr(obj, attr, 999)

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

"""
Objective Function Strategy (Strategy Pattern)

Defines scoring strategies for portfolio optimization.
Eliminates duplication of strategy logic across solvers.
"""

from __future__ import annotations

import inspect
from typing import Any, ClassVar, Protocol, cast

try:
    import numpy_financial as npf
except ModuleNotFoundError:  # pragma: no cover
    npf = None

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import OptimizationStrategy
from fhs.core.services.optimization.scoring.portfolio_metrics import (
    MIN_STD_DEV,
    PortfolioMetrics,
)


def _npv(rate: float, cashflows: list[float]) -> float:
    """Compute NPV with numpy_financial when available, otherwise locally."""
    if npf is not None:
        return float(npf.npv(rate, cashflows))
    return float(  # pragma: no cover - defensive
        sum(
            float(cashflow) / ((1.0 + float(rate)) ** period)
            for period, cashflow in enumerate(cashflows)
        )
    )


class ObjectiveFunction(Protocol):
    """
    Protocol for objective functions.

    Each strategy defines how to score a portfolio for optimization.
    """

    def score_portfolio(self, metrics: PortfolioMetrics) -> float:
        """Score a portfolio based on its metrics."""
        ...

    def score_feature(self, feature: Feature, result: SimulationResult) -> float:
        """Score an individual feature for greedy/ILP proxy optimization.

        For non-additive portfolio objectives this is an approximation.
        Exact portfolio quality is determined from full scenario aggregation.
        """
        ...

    @property
    def name(self) -> str:
        """Strategy name."""
        ...


class VarFloorObjective:
    """
    Maximize VaR95 (worst-case business value at 95% confidence).

    Conservative strategy focusing on downside protection.
    """

    @property
    def name(self) -> str:
        return "var_floor"

    @staticmethod
    def score_portfolio(metrics: PortfolioMetrics) -> float:
        """Return VaR95 as score (higher is better)."""
        return metrics.var_95

    @staticmethod
    def score_feature(feature: Feature, result: SimulationResult) -> float:
        """
        Score feature by net VaR95 (VaR95 - development cost).

        This is a linear proxy for `var_floor` selection.
        The true portfolio VaR95 objective is non-linear with respect to
        feature selection when correlation/scenario aggregation is considered.
        """
        return result.business_value_at_risk_95 - feature.development_cost


class ExpectedValueObjective:
    """
    Maximize expected portfolio business value.

    Classic expected value optimization.
    """

    @property
    def name(self) -> str:
        return "expected"

    @staticmethod
    def score_portfolio(metrics: PortfolioMetrics) -> float:
        """Return expected business value as score."""
        return metrics.expected

    @staticmethod
    def score_feature(feature: Feature, result: SimulationResult) -> float:
        """Score feature by net expected business value."""
        return result.expected_business_value - feature.development_cost


class SharpeRatioObjective:
    """
    Maximize Sharpe ratio (risk-adjusted return).

    Balances return against volatility.
    """

    @property
    def name(self) -> str:
        return "sharpe"

    @staticmethod
    def score_portfolio(metrics: PortfolioMetrics) -> float:
        """Return Sharpe ratio (expected / std_dev)."""
        return metrics.sharpe_ratio

    @staticmethod
    def score_feature(feature: Feature, result: SimulationResult) -> float:
        """
        Score feature by individual Sharpe ratio.

        Note: This is a linearizable proxy. True portfolio Sharpe is non-linear
        and depends on covariance/correlation effects captured only in full
        portfolio evaluation.
        """
        std = result.std * feature.business_value_per_conversion
        net_business_value = result.expected_business_value - feature.development_cost

        if std > MIN_STD_DEV:
            return net_business_value / std
        return net_business_value  # pragma: no cover - defensive


class NpvYear1Objective:
    """
    Maximize Year-1 NPV: discounted (BV − OpEx) minus upfront investment.

    Cashflow model (consistent with NB 03 Option A):
        Year 0: −development_cost
        Year 1: (expected_business_value − annual_operating_cost) / (1 + r)

    This objective remains linear/additive per feature, so ILP can optimize it
    directly without changing the linear solver formulation.
    """

    def __init__(self, discount_rate: float = 0.08):
        self._rate = float(discount_rate)

    @property
    def name(self) -> str:
        return "npv_year1"

    @staticmethod
    def score_portfolio(metrics: PortfolioMetrics) -> float:
        """Return expected portfolio revenue metric for non-ILP evaluation paths."""
        return metrics.expected  # pragma: no cover - defensive

    def score_feature(self, feature: Feature, result: SimulationResult) -> float:
        """Year-1 NPV: discounted (BV − OpEx) minus development cost."""
        cashflows = [
            -feature.development_cost,
            result.expected_business_value - feature.annual_operating_cost,
        ]
        return _npv(self._rate, cashflows)


class NpvThreeYearObjective:
    """
    Maximize 3-year NPV with annual growth, OpEx, and yearly discounting.

    Cashflow model (consistent with NB 03 Option A):
        Year 0: −development_cost
        Year t: (BV_base × (1+g)^(t-1) − annual_operating_cost) / (1+r)^t

    Uses feature-level additive approximation so ILP can optimize directly.
    """

    def __init__(self, discount_rate: float = 0.08):
        self._rate = float(discount_rate)

    @property
    def name(self) -> str:
        return "npv_3year"

    @staticmethod
    def score_portfolio(metrics: PortfolioMetrics) -> float:
        """Return expected portfolio revenue metric for non-ILP evaluation paths."""
        return metrics.expected  # pragma: no cover - defensive

    def score_feature(self, feature: Feature, result: SimulationResult) -> float:
        """3-year NPV: discounted (BV − OpEx) with growth minus development cost."""
        base = result.expected_business_value
        growth = feature.annual_growth_rate
        opex = feature.annual_operating_cost

        cashflows = [-feature.development_cost] + [
            base * (1 + growth) ** (year - 1) - opex for year in range(1, 4)
        ]
        return _npv(self._rate, cashflows)


class ObjectiveFunctionFactory:
    """
    Factory for creating objective functions.

    Centralizes strategy instantiation and validation.
    """

    _STRATEGIES: ClassVar[dict[str, type[Any]]] = {
        "var_floor": VarFloorObjective,
        "expected": ExpectedValueObjective,
        "sharpe": SharpeRatioObjective,
        "npv_year1": NpvYear1Objective,
        "npv_3year": NpvThreeYearObjective,
    }

    @classmethod
    # noinspection PyTypeHintsInspection
    def create(
        cls,
        strategy: str | OptimizationStrategy,
        **kwargs,
    ) -> ObjectiveFunction:
        """
        Create objective function for given strategy.

        Args:
            strategy: Strategy name or enum value

        Returns:
            Concrete objective function implementation

        Raises:
            ValueError: If strategy is unknown

        Example:
            >>> obj_fn = ObjectiveFunctionFactory.create("var_floor")
            >>> obj_fn.name
            'var_floor'
        """
        strategy_name = cls._normalize_strategy(strategy)

        if strategy_name not in cls._STRATEGIES:
            valid = tuple(cls._STRATEGIES.keys())
            raise ValueError(
                f"Unknown strategy '{strategy_name}'. Valid options: {valid}"
            )

        strategy_type = cls._STRATEGIES[strategy_name]

        if not kwargs:
            return cast(ObjectiveFunction, strategy_type())

        # Pass only supported constructor kwargs to stay backward compatible
        # with objectives that have no configurable parameters.
        signature = inspect.signature(strategy_type)
        accepts_var_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in signature.parameters.values()
        )
        if accepts_var_kwargs:
            return cast(
                ObjectiveFunction, strategy_type(**kwargs)
            )  # pragma: no cover - defensive

        accepted = {
            key: value for key, value in kwargs.items() if key in signature.parameters
        }
        return cast(ObjectiveFunction, strategy_type(**accepted))

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _normalize_strategy(strategy: str | OptimizationStrategy) -> str:
        """Normalize strategy to string representation."""
        if isinstance(strategy, OptimizationStrategy):
            return strategy.value
        return strategy

    @classmethod
    def supported_strategies(cls) -> tuple[str, ...]:
        """Return tuple of supported strategy names."""
        return tuple(cls._STRATEGIES.keys())

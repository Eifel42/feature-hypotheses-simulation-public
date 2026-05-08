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
Portfolio Metrics Calculator (NumPy-Optimized)

Centralized calculation of portfolio statistics using vectorized operations.
Eliminates code duplication across solver implementations.
"""

from dataclasses import dataclass

import numpy as np

from fhs.core.services import RiskCalculator

# Constants
VAR_PERCENTILE = 5.0  # 95% VaR = 5th percentile
MIN_STD_DEV = 1e-10  # Numerical stability threshold


@dataclass(frozen=True)
class PortfolioMetrics:
    """
    Immutable container for portfolio performance metrics.

    All metrics are computed from scenario results using vectorized NumPy operations.
    """

    expected: float
    var_95: float
    cvar_95: float
    std_dev: float

    @property
    def sharpe_ratio(self) -> float:
        """Sharpe ratio (expected / std_dev), safe division."""
        return self.expected / self.std_dev if self.std_dev > MIN_STD_DEV else 0.0


class PortfolioMetricsCalculator:
    """
    Calculator for portfolio-level metrics using NumPy vectorization.

    Centralizes metric computation to eliminate duplication across
    Exact, Greedy, and ILP solvers.
    """

    def __init__(self, risk_calculator: RiskCalculator):
        """
        Initialize calculator.

        Args:
            risk_calculator: Risk calculator for VaR/CVaR computation
        """
        self.calculator = risk_calculator

    def calculate(self, portfolio_scenarios: np.ndarray) -> PortfolioMetrics:
        """
        Calculate all portfolio metrics from scenario array.

        Uses vectorized NumPy operations for maximum performance.

        Args:
            portfolio_scenarios: 1D array of portfolio business value scenarios

        Returns:
            PortfolioMetrics value object with all computed metrics

        Example:
            >>> calc = PortfolioMetricsCalculator(risk_calc)
            >>> scenarios = np.array([100, 120, 80, 150])
            >>> metrics = calc.calculate(scenarios)
            >>> metrics.expected
            112.5
        """
        # Vectorized calculations (single pass)
        expected = float(np.mean(portfolio_scenarios))
        std_dev = float(np.std(portfolio_scenarios, ddof=1))  # Sample std
        var_95 = self.calculator.calculate_var(
            portfolio_scenarios, confidence_level=0.95
        )
        cvar_95 = self.calculator.calculate_cvar(
            portfolio_scenarios, confidence_level=0.95
        )

        return PortfolioMetrics(
            expected=expected,
            var_95=var_95,
            cvar_95=cvar_95,
            std_dev=std_dev,
        )

    def calculate_batch(
        self, scenarios_list: list[np.ndarray]
    ) -> list[PortfolioMetrics]:
        """
        Calculate metrics for multiple portfolios in batch.

        Args:
            scenarios_list: List of scenario arrays

        Returns:
            List of PortfolioMetrics objects
        """
        return [
            self.calculate(scenarios) for scenarios in scenarios_list
        ]  # pragma: no cover - defensive

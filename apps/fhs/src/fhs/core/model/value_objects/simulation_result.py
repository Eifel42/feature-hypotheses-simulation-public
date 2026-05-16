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
SimulationResult Value Object

Contains the SimulationResult class with 25+ computed properties.
"""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class SimulationResult(BaseModel):
    """
    Result of a Monte Carlo simulation.

    Attributes:
        feature_name: Name of the simulated feature
        expected_value: Expected value from simulation
        business_value_per_conversion: Business value per conversion
        development_cost: Development cost
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    feature_name: str = Field(..., min_length=1)
    expected_value: float = Field(default=0.0)
    business_value_per_conversion: float = Field(default=1.0)
    development_cost: float = Field(default=0.0)
    installment_years: int = Field(default=1, ge=1)
    _data: np.ndarray = np.array([], dtype=float)
    _var_95_value: float | None = None
    _scenarios_count: int | None = None

    # noinspection PyTypeHintsInspection
    def __init__(
        self,
        feature_name: str,
        results: np.ndarray | list | None = None,
        scenarios: int | None = None,
        expected_value: float = 0.0,
        var_95: float | None = None,
        business_value_per_conversion: float = 1.0,
        development_cost: float = 0.0,
        installment_years: int = 1,
    ):
        super().__init__(
            feature_name=feature_name,
            expected_value=expected_value,
            business_value_per_conversion=business_value_per_conversion,
            development_cost=development_cost,
            installment_years=installment_years,
        )

        if results is not None:
            self._data = np.asarray(results, dtype=float)
        else:
            self._data = np.array([], dtype=float)

        inferred_scenarios = len(self._data) if len(self._data) > 0 else None
        self._scenarios_count = (
            scenarios if scenarios is not None else inferred_scenarios
        )
        self._var_95_value = var_95

    @property
    def scenarios(self) -> int | None:
        """Number of simulation scenarios."""
        return self._scenarios_count

    @property
    def results(self) -> list:
        """Simulation results as a plain Python list."""
        return self._data.tolist() if len(self._data) > 0 else []

    @property
    def results_array(self) -> np.ndarray:
        """Simulation results as a NumPy array."""
        return self._data

    @property
    def risk_metrics(self) -> dict[str, float]:
        """Comprehensive risk metrics for the simulation."""
        results_arr = self._data
        if len(results_arr) == 0:
            return {}

        return {
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "expected": self.expected_value,
            "worst_case": float(np.min(results_arr)),
            "best_case": float(np.max(results_arr)),
            "std_dev": float(np.std(results_arr)),
            "median": float(np.median(results_arr)),
        }

    @property
    def var_95(self) -> float:
        """Minimum Outcome at 95% Confidence (Gain-based VaR).

        This is the 5th percentile of the distribution.
        """
        if self._var_95_value is not None:
            return self._var_95_value
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        return float(np.percentile(results_arr, 5))

    @property
    def loss_var_95(self) -> float:
        """Loss-based VaR at 95%: ``expected_value - var_95``."""
        return self.expected_value - self.var_95

    @property
    def cvar_95(self) -> float:
        """Expected Outcome in the Worst 5% of Scenarios (Expected Shortfall)."""
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        threshold = np.percentile(results_arr, 5)
        tail = results_arr[results_arr <= threshold]
        return float(np.mean(tail)) if len(tail) > 0 else float(threshold)

    @property
    def mean(self) -> float:
        """Arithmetic mean of simulated results."""
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        return float(np.mean(results_arr))

    @property
    def median(self) -> float:
        """Median of simulated results."""
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        return float(np.median(results_arr))

    @property
    def std(self) -> float:
        """Standard deviation of simulated results."""
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        return float(np.std(results_arr))

    def _get_percentile(self, p: float) -> float:
        """Calculate a percentile from simulation results."""
        results_arr = self._data
        if len(results_arr) == 0:
            return 0.0
        return float(np.percentile(results_arr, p))

    @property
    def p5(self) -> float:
        """Alias for var_95 (minimum outcome at 95% confidence)."""
        return self.var_95

    @property
    def p10(self) -> float:
        """10th percentile"""
        return self._get_percentile(10)

    @property
    def p90(self) -> float:
        """90th percentile"""
        return self._get_percentile(90)

    @property
    def p95(self) -> float:
        """95th percentile"""
        return self._get_percentile(95)

    @property
    def percentiles(self) -> dict[str, float]:
        """Key percentiles (p5 through p95) for risk analysis."""
        results_arr = self._data
        if len(results_arr) == 0:
            return {}

        keys = ["p5", "p10", "p25", "p50", "p75", "p90", "p95"]
        pcts = [5, 10, 25, 50, 75, 90, 95]
        return {k: self._get_percentile(p) for k, p in zip(keys, pcts, strict=False)}

    @property
    def confidence_interval(self) -> list[float]:
        """90% confidence interval ``[p5, p95]``."""
        return [self._get_percentile(5), self._get_percentile(95)]

    @property
    def expected_business_value(self) -> float:
        """Expected business value: ``expected_value * business_value_per_conversion``."""
        return self.expected_value * self.business_value_per_conversion

    @property
    def business_value_at_risk_95(self) -> float:
        """Minimum Business Value at 95% Confidence (Business-Value-at-Risk)."""
        return self.var_95 * self.business_value_per_conversion

    @property
    def annual_installment(self) -> float:
        """Annual installment of development cost (straight-line).

        Returns development_cost / installment_years.
        With the default of 1 year this equals the full development cost.
        """
        return self.development_cost / self.installment_years

    @property
    def net_value_at_risk_95(self) -> float:
        """Minimum Net Value at 95% Confidence (after annual installment)."""
        return self.business_value_at_risk_95 - self.annual_installment

    @property
    def cvar_95_net_value(self) -> float:
        """Average Net Value in the Worst 5% of Scenarios (after annual installment)."""
        return (
            self.cvar_95 * self.business_value_per_conversion
        ) - self.annual_installment

    @property
    def business_value_risk_metrics(self) -> dict[str, float]:
        """Risk metrics scaled to business value."""
        bv = self.business_value_per_conversion
        dep = self.annual_installment
        results_arr = self._data
        if len(results_arr) == 0:
            return {}

        return {
            "expected_business_value": self.expected_value * bv,
            "business_value_at_risk_95": self.var_95 * bv,
            "cvar_95_business_value": self.cvar_95 * bv,
            "minimum_expected_business_value_95": self.var_95 * bv,
            "average_worst_case_business_value_95": self.cvar_95 * bv,
            "minimum_net_value_95": (self.var_95 * bv) - dep,
            "average_worst_case_net_value_95": (self.cvar_95 * bv) - dep,
            "worst_case_business_value": float(np.min(results_arr)) * bv,
            "best_case_business_value": float(np.max(results_arr)) * bv,
            "business_value_std_dev": float(np.std(results_arr)) * bv,
            "median_business_value": float(np.median(results_arr)) * bv,
        }

    @property
    def roi(self) -> float:
        """Return on Investment (based on annual installment)."""
        if self.annual_installment <= 0:
            return 0.0
        return (
            self.expected_business_value - self.annual_installment
        ) / self.annual_installment

    @property
    def net_value(self) -> float:
        """Net value: ``expected_business_value - annual_installment``."""
        return self.expected_business_value - self.annual_installment

    @property
    def profit_margin(self) -> float:
        """Profit margin (based on annual installment)."""
        if self.expected_business_value <= 0:
            return 0.0
        return (
            self.expected_business_value - self.annual_installment
        ) / self.expected_business_value

    @property
    def risk_ratio(self) -> float:
        """Relative spread: standard deviation divided by expected value."""
        expected = float(self.expected_value)
        spread = float(self.std)
        return (spread / expected) if expected > 0 else float("inf")

    def risk_verdict(self) -> tuple[str, str]:
        """Return risk label and explanation derived from ``risk_ratio``."""
        ratio = self.risk_ratio
        if ratio < 0.15:
            return "LOW RISK", "High confidence in this estimate"
        if ratio < 0.30:
            return "MODERATE RISK", "Results have meaningful spread"
        return "HIGH RISK", "Wide range of outcomes possible"

    def risk_classification(self) -> tuple[str, str]:
        """Return risk label and traffic-light icon."""
        label, _ = self.risk_verdict()
        icon = {
            "LOW RISK": "🟢",
            "MODERATE RISK": "🟡",
            "HIGH RISK": "🔴",
        }.get(label, "⚪")
        return label, icon

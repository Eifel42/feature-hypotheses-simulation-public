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
Risk Calculator for Feature Hypotheses Simulation

Provides risk measurement calculations including VaR, CVaR, and statistical metrics.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import stats

from fhs.core.model import DEFAULT_CONFIG
from fhs.core.model.exceptions import (
    InsufficientDataError,
    ValidationError,
)
from fhs.core.model.value_objects import ConfidenceLevel, RiskMetric
from fhs.core.model.value_objects.feature_ranking_metrics import (
    FeatureRankingMetrics,
)
from fhs.core.typing_utils import to_float_array

if TYPE_CHECKING:
    from fhs.core.model.value_objects.loss_profile import LossProfile

logger = logging.getLogger("fhs.risk_calculator")
DEFAULT_BOOTSTRAP_SEED = 42
CONFIDENCE_LEVEL_ERROR = "Confidence level must be between 0 and 1"

# ---------------------------------------------------------------------------
# Module-level LRU cache for deterministic calculations.
# Activation and size are read from DEFAULT_CONFIG.
# np.ndarray is not hashable — arrays are encoded via tobytes() + metadata as
# keys, so that identical data is served from the cache.
# ---------------------------------------------------------------------------
_cache: Any = (
    lru_cache(maxsize=DEFAULT_CONFIG.CACHE_MAX_SIZE)
    if DEFAULT_CONFIG.ENABLE_CACHING
    else (lambda f: f)  # type: ignore[return-value]
)


@_cache
def _var_cached(
    data_bytes: bytes, shape: tuple, dtype: str, confidence: float
) -> float:
    """Cached VaR calculation based on an array key."""
    arr = np.frombuffer(data_bytes, dtype=np.dtype(dtype)).reshape(shape)
    return float(np.percentile(arr, (1 - confidence) * 100))


@_cache
def _cvar_cached(
    data_bytes: bytes, shape: tuple, dtype: str, confidence: float
) -> float:
    """Cached CVaR calculation based on an array key."""
    arr = np.frombuffer(data_bytes, dtype=np.dtype(dtype)).reshape(shape)
    threshold = _var_cached(data_bytes, shape, dtype, confidence)
    tail = arr[arr <= threshold]
    return float(np.mean(tail)) if len(tail) > 0 else threshold


@_cache
def _percentile_cached(
    data_bytes: bytes, shape: tuple, dtype: str, percentile: float
) -> float:
    """Cached percentile calculation."""
    arr = np.frombuffer(data_bytes, dtype=np.dtype(dtype)).reshape(shape)
    return float(np.percentile(arr, percentile))


def _array_key(arr: np.ndarray) -> tuple[bytes, tuple[int, ...], str]:
    """Creates a hashable key from a numpy array."""
    contiguous = np.ascontiguousarray(arr)
    return contiguous.tobytes(), contiguous.shape, contiguous.dtype.str


class RiskCalculator:
    """Financial risk calculator for simulation results.

    Provides Value at Risk (VaR), Conditional VaR (CVaR / Expected Shortfall),
    percentile analysis, and bootstrap confidence intervals.
    """

    # Minimum scenarios recommended for stable tail metrics.
    # Below this threshold a warning is emitted, but the calculation still runs.
    _TAIL_SCENARIOS_WARN_THRESHOLD: int = 5_000
    # Confidence level at which tail-metric warnings are triggered.
    _TAIL_CONFIDENCE_WARN: float = 0.99

    @staticmethod
    def calculate_var(scenarios: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Gain-based Value at Risk (Business-Value-at-Risk / outcome floor).

        Returns the ``(1 - confidence_level)``-th percentile of the outcome
        distribution.  This is an *outcome floor*: with probability
        ``confidence_level`` the actual result is at least this large.

        Note: This is the **opposite sign convention** from financial VaR,
        which measures a maximum *loss*.  For the loss interpretation compute
        ``expected_value - calculate_var(...)``.

        Args:
            scenarios: Simulated results
            confidence_level: Confidence level (e.g. 0.95 for 95%)

        Returns:
            float: The (1 - confidence_level) percentile of simulated outcomes.
        """
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValidationError(
                CONFIDENCE_LEVEL_ERROR,
                field="confidence_level",
                value=confidence_level,
            )

        scenarios = to_float_array(scenarios)
        n = len(scenarios)
        if (
            confidence_level >= RiskCalculator._TAIL_CONFIDENCE_WARN
            and n < RiskCalculator._TAIL_SCENARIOS_WARN_THRESHOLD
        ):
            logger.warning(
                "VaR at confidence_level=%.2f requested with only %d scenarios. "
                "Tail-percentile estimates may vary by >1%%. "
                "Consider using scenarios >= %d for stable results.",
                confidence_level,
                n,
                RiskCalculator._TAIL_SCENARIOS_WARN_THRESHOLD,
            )

        key_bytes, key_shape, key_dtype = _array_key(scenarios)
        return float(_var_cached(key_bytes, key_shape, key_dtype, confidence_level))

    @staticmethod
    def calculate_cvar(scenarios: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Conditional Value at Risk (Expected Shortfall)

        Args:
            scenarios: Simulated results
            confidence_level: Confidence level

        Returns:
            CVaR value: Expected loss beyond VaR
        """
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValidationError(
                CONFIDENCE_LEVEL_ERROR,
                field="confidence_level",
                value=confidence_level,
            )

        scenarios = to_float_array(scenarios)
        n = len(scenarios)
        if (
            confidence_level >= RiskCalculator._TAIL_CONFIDENCE_WARN
            and n < RiskCalculator._TAIL_SCENARIOS_WARN_THRESHOLD
        ):
            logger.warning(
                "CVaR at confidence_level=%.2f requested with only %d scenarios. "
                "Expected Shortfall in the tail may vary by >1%%. "
                "Consider using scenarios >= %d for stable CVaR_99 results.",
                confidence_level,
                n,
                RiskCalculator._TAIL_SCENARIOS_WARN_THRESHOLD,
            )

        key_bytes, key_shape, key_dtype = _array_key(scenarios)
        return float(_cvar_cached(key_bytes, key_shape, key_dtype, confidence_level))

    @staticmethod
    # noinspection PyTypeHintsInspection
    def calculate_risk_metric(
        scenarios: np.ndarray,
        confidence_level: float | ConfidenceLevel = 0.95,
    ) -> RiskMetric:
        """Calculate a typed RiskMetric value object.

        This complements ``calculate_var``/``calculate_cvar`` with a single
        domain-friendly object return type.
        """
        level = (
            confidence_level.level
            if isinstance(confidence_level, ConfidenceLevel)
            else confidence_level
        )
        var = RiskCalculator.calculate_var(scenarios, level)
        cvar = RiskCalculator.calculate_cvar(scenarios, level)
        return RiskMetric(var=var, cvar=cvar, confidence_level=level)

    @staticmethod
    def calculate_risk_metrics(scenarios: np.ndarray) -> dict[str, float]:
        """
        All important risk metrics using scipy.stats.describe.

        Args:
            scenarios: Simulated results

        Returns:
            Dictionary with all risk metrics.
        """
        scenarios = to_float_array(scenarios)
        scenarios_clean = scenarios[~np.isnan(scenarios)]

        if len(scenarios_clean) == 0:
            raise InsufficientDataError(
                "No valid scenarios provided",
                required=1,
                provided=len(scenarios_clean),
            )

        std_val = float(np.std(scenarios_clean))

        if std_val == 0:
            # Degenerate case: all values identical — skip describe() to
            # avoid scipy precision-loss warnings.
            mean_val = float(scenarios_clean[0])
            skewness_val = 0.0
            kurtosis_val = 0.0
            min_val = max_val = mean_val
        else:
            desc = stats.describe(scenarios_clean)
            mean_val = float(desc.mean)
            std_val = float(np.sqrt(desc.variance))
            skewness_val = float(desc.skewness)
            kurtosis_val = float(desc.kurtosis)
            min_val = float(desc.minmax[0])
            max_val = float(desc.minmax[1])

        var_95 = RiskCalculator.calculate_var(scenarios_clean, 0.95)
        cvar_95 = RiskCalculator.calculate_cvar(scenarios_clean, 0.95)

        return {
            "expected": float(mean_val),
            "var_95": var_95,
            "var_99": RiskCalculator.calculate_var(scenarios_clean, 0.99),
            "cvar_95": cvar_95,
            "cvar_99": RiskCalculator.calculate_cvar(scenarios_clean, 0.99),
            "minimum_expected_95": var_95,
            "average_worst_case_95": cvar_95,
            "std_dev": std_val,
            "skewness": skewness_val,
            "kurtosis": kurtosis_val,
            "min": min_val,
            "max": max_val,
            "median": float(np.median(scenarios_clean)),
        }

    @staticmethod
    def calculate_percentile(scenarios: np.ndarray, percentile: float) -> float:
        """
        Calculate percentile of scenarios

        Args:
            scenarios: Scenario results
            percentile: Percentile value (0-100)

        Returns:
            Percentile value

        Raises:
            ValueError: If percentile is not between 0 and 100
        """
        if percentile < 0 or percentile > 100:
            raise ValidationError(
                "Percentile must be between 0 and 100",
                field="percentile",
                value=percentile,
            )

        scenarios = to_float_array(scenarios)
        key_bytes, key_shape, key_dtype = _array_key(scenarios)
        return float(_percentile_cached(key_bytes, key_shape, key_dtype, percentile))

    @staticmethod
    # noinspection PyTypeHintsInspection
    def bootstrap_confidence_interval(
        scenarios: np.ndarray,
        confidence_level: float = 0.95,
        n_bootstrap: int = 1000,
        rng: np.random.Generator | None = None,
    ) -> tuple[float, float]:
        """
        Calculate bootstrap confidence interval using scipy.stats.bootstrap.

        Uses the BCa (bias-corrected and accelerated) method for more
        accurate confidence intervals than the basic percentile method.

        Args:
            scenarios: Scenario results
            confidence_level: Confidence level (0-1)
            n_bootstrap: Number of bootstrap samples
            rng: Optional numpy Generator for reproducible bootstrap results

        Returns:
            Tuple of (lower_bound, upper_bound)

        Raises:
            ValueError: If confidence_level is not between 0 and 1
            ValueError: If n_bootstrap is not positive
        """
        if confidence_level <= 0 or confidence_level >= 1:
            raise ValidationError(
                CONFIDENCE_LEVEL_ERROR,
                field="confidence_level",
                value=confidence_level,
            )

        if n_bootstrap <= 0:
            raise ValidationError(
                "Number of bootstrap samples must be positive",
                field="n_bootstrap",
                value=n_bootstrap,
            )

        import warnings

        scenarios = to_float_array(scenarios)
        rng = rng if rng is not None else np.random.default_rng(DEFAULT_BOOTSTRAP_SEED)

        # BCa is preferred but falls back to percentile for degenerate data
        # (e.g. all identical values) where BCa cannot be computed.
        bootstrap_fn = stats.bootstrap  # type: ignore[attr-defined]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            try:
                result = bootstrap_fn(
                    (scenarios,),
                    statistic=np.mean,
                    n_resamples=n_bootstrap,
                    confidence_level=confidence_level,
                    random_state=rng,
                    method="BCa",
                )
            except (
                ValueError,
                RuntimeError,
                np.linalg.LinAlgError,
            ):  # pragma: no cover - defensive
                result = bootstrap_fn(  # pragma: no cover - defensive
                    (scenarios,),
                    statistic=np.mean,
                    n_resamples=n_bootstrap,
                    confidence_level=confidence_level,
                    random_state=rng,
                    method="percentile",
                )

        return float(result.confidence_interval.low), float(
            result.confidence_interval.high
        )

    @staticmethod
    def calculate_risk_ratio(
        expected: float, var_95: float, clamp: bool = True
    ) -> float:
        """
        Calculate risk ratio: (expected - var_95) / expected

        Risk ratio represents the proportion of expected value that is "at risk"
        in the worst 5% of scenarios. A ratio of 0 means no downside risk,
        while 1 means total risk (VaR is zero or negative).

        This replaces 3 duplicated implementations across portfolio_advisor,
        feature_assessment, and ranking modules.

        Args:
            expected: Expected value (mean)
            var_95: Value at Risk at 95% confidence
            clamp: If True, clamp result to [0, 1] (default: True)

        Returns:
            Risk ratio as float. If clamped: 0.0 (no risk) to 1.0 (total risk)

        Example:
            >>> RiskCalculator.calculate_risk_ratio(100, 80)
            0.2  # 20% of expected value is at risk
            >>> RiskCalculator.calculate_risk_ratio(100, 120)
            0.0  # No risk (VaR exceeds expected, clamped to 0)
        """
        if expected == 0:
            return 0.0  # pragma: no cover - defensive

        ratio = (expected - var_95) / expected

        if clamp:
            return max(0.0, min(1.0, ratio))
        return ratio  # pragma: no cover - defensive

    @staticmethod
    def calculate_hhi(shares: list[float] | dict[str, float]) -> float:
        """
        Calculate Herfindahl-Hirschman Index (HHI) for concentration risk.

        HHI measures market/portfolio concentration. Values range from 0 (perfect
        diversity) to 1 (complete concentration in one item).

        Thresholds (common interpretation):
        - HHI < 0.15: Low concentration (diversified)
        - 0.15 ≤ HHI < 0.25: Moderate concentration
        - HHI ≥ 0.25: High concentration

        This replaces duplicated implementations in portfolio_advisor and ranking.

        Args:
            shares: Either list of shares or dict mapping names to shares.
                    Shares should sum to 1.0 but will be normalized if not.

        Returns:
            HHI value (0.0 to 1.0)

        Example:
            >>> RiskCalculator.calculate_hhi([0.5, 0.3, 0.2])
            0.38  # Moderate concentration
            >>> RiskCalculator.calculate_hhi({"A": 0.33, "B": 0.33, "C": 0.34})
            0.33  # Equal distribution
        """
        # Convert dict to list if needed and keep a list variable for typing.
        share_values = list(shares.values()) if isinstance(shares, dict) else shares

        if not share_values:
            return 0.0  # pragma: no cover - defensive

        # Normalize shares to sum to 1.0
        total = sum(share_values)
        if total == 0:
            return 0.0  # pragma: no cover - defensive

        arr = np.asarray(share_values, dtype=float) / total

        # HHI = sum of squared shares
        return float(np.sum(arr**2))

    @staticmethod
    def feature_ranking_metrics(
        *,
        feature_name: str,
        bv_scenarios: np.ndarray,
        development_cost: float,
        confidence_level: float = 0.95,
        epsilon: float = 1.0,
    ) -> FeatureRankingMetrics:
        """Compute a multi-view risk profile for a single feature.

        Returns both gain-convention metrics (BV-floor, BV-CVaR) and
        loss-convention metrics (loss-VaR, loss-CVaR) plus normalized ranking
        metrics (risk_ratio, rorac, risk_adjusted_roi) from a Business-Value
        scenario array.

        Args:
            feature_name: Label of the feature being profiled.
            bv_scenarios: Simulated Business-Value outcomes.
            development_cost: Expected development cost; used for
                risk-adjusted-ROI. Non-positive costs yield ``+inf``.
            confidence_level: Tail confidence level for VaR/CVaR (default 0.95).
            epsilon: Lower bound for ``loss_var`` used in the RoRaC
                denominator to keep the ratio finite when the feature has a
                near-zero downside (default 1.0 currency unit).

        Returns:
            FeatureRankingMetrics: immutable profile with all ranking metrics.
        """
        arr = to_float_array(bv_scenarios)
        expected = float(np.mean(arr))
        bv_var = RiskCalculator.calculate_var(arr, confidence_level)
        bv_cvar = RiskCalculator.calculate_cvar(arr, confidence_level)

        loss_var = max(0.0, expected - bv_var)
        loss_cvar = max(0.0, expected - bv_cvar)

        risk_ratio = loss_var / expected if expected > 0 else 0.0
        risk_ratio = min(1.0, max(0.0, risk_ratio))

        rorac = expected / max(loss_var, epsilon)

        if development_cost > 0:
            risk_adjusted_roi = bv_var / development_cost
        else:
            risk_adjusted_roi = float("inf")

        return FeatureRankingMetrics(
            feature_name=feature_name,
            confidence_level=confidence_level,
            expected_bv=expected,
            bv_var=bv_var,
            bv_cvar=bv_cvar,
            loss_var=loss_var,
            loss_cvar=loss_cvar,
            risk_ratio=risk_ratio,
            rorac=rorac,
            risk_adjusted_roi=risk_adjusted_roi,
        )

    @staticmethod
    def loss_profile(
        pnl_values: np.ndarray,
        *,
        confidence: float = 0.95,
    ) -> LossProfile:
        """Calculate loss-space and P&L-space risk profile from P&L distribution.

        Args:
            pnl_values: Profit & Loss scenarios (numpy array)
            confidence: Confidence level for VaR/CVaR (default: 0.95)

        Returns:
            LossProfile with P&L and loss metrics
        """
        from fhs.core.model import LossProfile

        pnl_values = to_float_array(pnl_values)

        if len(pnl_values) == 0:
            return LossProfile(  # pragma: no cover - defensive
                confidence=confidence,
                pnl_expected=0.0,
                pnl_var=0.0,
                pnl_cvar=0.0,
                loss_expected=0.0,
                loss_var=0.0,
                loss_cvar=0.0,
                worst_case_loss=0.0,
            )

        pnl_var = float(np.percentile(pnl_values, (1.0 - confidence) * 100.0))
        pnl_tail = pnl_values[pnl_values <= pnl_var]

        losses = -pnl_values
        loss_var = float(np.percentile(losses, confidence * 100.0))
        loss_tail = losses[losses >= loss_var]

        return LossProfile(
            confidence=confidence,
            pnl_expected=float(np.mean(pnl_values)),
            pnl_var=pnl_var,
            pnl_cvar=float(np.mean(pnl_tail)) if len(pnl_tail) > 0 else pnl_var,
            loss_expected=float(np.mean(np.clip(losses, 0.0, None))),
            loss_var=loss_var,
            loss_cvar=float(np.mean(loss_tail)) if len(loss_tail) > 0 else loss_var,
            worst_case_loss=float(np.max(losses)),
        )

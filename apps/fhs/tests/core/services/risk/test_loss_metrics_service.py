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

"""Tests for LossMetricsService."""

import numpy as np
import pytest

from fhs.core.model.value_objects import LossMetrics, LossProfile
from fhs.core.services.risk.loss_metrics import LossMetricsService


def test_from_subset_pnl_function_builds_metrics() -> None:
    calls: list[tuple[np.ndarray, float]] = []

    def loss_profile_function(pnl: np.ndarray, confidence: float) -> LossProfile:
        calls.append((pnl.copy(), confidence))
        return LossProfile(
            confidence=confidence,
            pnl_expected=float(np.mean(pnl)),
            pnl_var=float(np.percentile(pnl, 5)),
            pnl_cvar=float(np.mean(pnl[pnl <= np.percentile(pnl, 5)])),
            loss_expected=10.0,
            loss_var=20.0,
            loss_cvar=30.0,
            worst_case_loss=40.0,
        )

    result = LossMetricsService.from_subset_pnl_function(
        selected=("F1", "F2"),
        delivery_gates={
            "F1": np.array([False, True, False, True], dtype=bool),
            "F2": np.array([False, False, True, True], dtype=bool),
        },
        development_cost_by_feature={"F1": 20_000.0, "F2": 30_000.0},
        pnl_function=lambda: np.array([100.0, -20.0, 50.0, -10.0], dtype=float),
        loss_profile_function=loss_profile_function,
        confidence=0.95,
    )

    assert isinstance(result, LossMetrics)
    assert len(calls) == 1
    assert calls[0][1] == pytest.approx(0.95)
    assert result.investment == pytest.approx(50_000.0)
    assert result.catastrophe_threshold == pytest.approx(50_000.0)
    assert result.catastrophe_probability == pytest.approx(0.25)
    assert result.cvar_loss == pytest.approx(30.0)


def test_from_subset_pnl_function_returns_zero_metrics_for_empty_selection() -> None:
    def loss_profile_function(pnl: np.ndarray, confidence: float) -> LossProfile:
        assert len(pnl) == 0
        return LossProfile(
            confidence=confidence,
            pnl_expected=0.0,
            pnl_var=0.0,
            pnl_cvar=0.0,
            loss_expected=0.0,
            loss_var=0.0,
            loss_cvar=0.0,
            worst_case_loss=0.0,
        )

    result = LossMetricsService.from_subset_pnl_function(
        selected=(),
        delivery_gates={},
        development_cost_by_feature={},
        pnl_function=lambda: np.array([1.0], dtype=float),
        loss_profile_function=loss_profile_function,
        confidence=0.95,
    )

    assert result.investment == pytest.approx(0.0)
    assert result.catastrophe_probability == pytest.approx(0.0)
    assert result.catastrophe_threshold == pytest.approx(0.0)
    assert result.cvar_loss == pytest.approx(0.0)


def test_from_subset_pnl_function_validates_confidence() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        LossMetricsService.from_subset_pnl_function(
            selected=("F1",),
            delivery_gates={"F1": np.array([True], dtype=bool)},
            development_cost_by_feature={"F1": 1.0},
            pnl_function=lambda: np.array([1.0], dtype=float),
            loss_profile_function=lambda pnl, confidence: LossProfile(
                confidence=confidence,
                pnl_expected=0.0,
                pnl_var=0.0,
                pnl_cvar=0.0,
                loss_expected=0.0,
                loss_var=0.0,
                loss_cvar=0.0,
                worst_case_loss=0.0,
            ),
            confidence=1.0,
        )


def test_from_subset_pnl_function_raises_on_missing_delivery_gate() -> None:
    """Test that missing delivery gate for a selected feature raises KeyError."""
    with pytest.raises(KeyError, match="Missing delivery gate"):
        LossMetricsService.from_subset_pnl_function(
            selected=("F1", "F2"),
            delivery_gates={"F1": np.array([True], dtype=bool)},  # F2 missing
            development_cost_by_feature={"F1": 1.0, "F2": 1.0},
            pnl_function=lambda: np.array([1.0], dtype=float),
            loss_profile_function=lambda pnl, confidence: LossProfile(
                confidence=confidence,
                pnl_expected=0.0,
                pnl_var=0.0,
                pnl_cvar=0.0,
                loss_expected=0.0,
                loss_var=0.0,
                loss_cvar=0.0,
                worst_case_loss=0.0,
            ),
            confidence=0.95,
        )


def test_from_subset_pnl_function_raises_on_length_mismatch() -> None:
    """Test that delivery gate length mismatch raises ValueError."""
    with pytest.raises(ValueError, match="Delivery gate length mismatch"):
        LossMetricsService.from_subset_pnl_function(
            selected=("F1",),
            delivery_gates={"F1": np.array([True, False], dtype=bool)},  # len 2
            development_cost_by_feature={"F1": 1.0},
            pnl_function=lambda: np.array([1.0, 2.0, 3.0], dtype=float),  # len 3
            loss_profile_function=lambda pnl, confidence: LossProfile(
                confidence=confidence,
                pnl_expected=0.0,
                pnl_var=0.0,
                pnl_cvar=0.0,
                loss_expected=0.0,
                loss_var=0.0,
                loss_cvar=0.0,
                worst_case_loss=0.0,
            ),
            confidence=0.95,
        )

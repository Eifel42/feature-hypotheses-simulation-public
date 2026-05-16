# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md

"""Tests for FeatureRankingMetrics value object."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from fhs.core.model.value_objects import FeatureRankingMetrics


def _valid_kwargs(**overrides) -> dict:
    base = {
        "feature_name": "Feature A",
        "confidence_level": 0.95,
        "expected_bv": 100_000.0,
        "bv_var": 80_000.0,
        "bv_cvar": 70_000.0,
        "loss_var": 20_000.0,
        "loss_cvar": 30_000.0,
        "risk_ratio": 0.2,
        "rorac": 5.0,
        "risk_adjusted_roi": 1.6,
    }
    base.update(overrides)
    return base


class TestFeatureRankingMetrics:
    def test_construct_with_valid_gain_and_loss_conventions(self) -> None:
        metrics = FeatureRankingMetrics(**_valid_kwargs())
        assert metrics.feature_name == "Feature A"
        assert metrics.expected_bv == 100_000.0
        assert metrics.bv_var == 80_000.0
        assert metrics.bv_cvar == 70_000.0

    def test_frozen_cannot_mutate_after_construction(self) -> None:
        metrics = FeatureRankingMetrics(**_valid_kwargs())
        with pytest.raises(ValidationError):
            metrics.expected_bv = 200_000.0  # type: ignore[misc]

    def test_confidence_level_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(confidence_level=-0.01))

    def test_confidence_level_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(confidence_level=1.01))

    def test_confidence_level_at_boundaries_accepted(self) -> None:
        m0 = FeatureRankingMetrics(**_valid_kwargs(confidence_level=0.0))
        m1 = FeatureRankingMetrics(**_valid_kwargs(confidence_level=1.0))
        assert m0.confidence_level == 0.0
        assert m1.confidence_level == 1.0

    def test_empty_feature_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(feature_name=""))

    def test_cvar_greater_than_var_raises_gain_convention(self) -> None:
        with pytest.raises(ValidationError, match="gain convention"):
            FeatureRankingMetrics(**_valid_kwargs(bv_var=80_000.0, bv_cvar=85_000.0))

    def test_loss_cvar_less_than_loss_var_raises_loss_convention(self) -> None:
        with pytest.raises(ValidationError, match="loss convention"):
            FeatureRankingMetrics(
                **_valid_kwargs(loss_var=30_000.0, loss_cvar=20_000.0)
            )

    def test_risk_ratio_below_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(risk_ratio=-0.01))

    def test_risk_ratio_above_one_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(risk_ratio=1.01))

    def test_negative_loss_var_raises(self) -> None:
        with pytest.raises(ValidationError):
            FeatureRankingMetrics(**_valid_kwargs(loss_var=-10.0))

    def test_loss_var_zero_is_valid(self) -> None:
        metrics = FeatureRankingMetrics(
            **_valid_kwargs(loss_var=0.0, loss_cvar=0.0, risk_ratio=0.0)
        )
        assert metrics.loss_var == 0.0

    def test_equal_bv_var_and_expected_produces_zero_loss_ratio(self) -> None:
        metrics = FeatureRankingMetrics(
            **_valid_kwargs(
                expected_bv=100_000.0,
                bv_var=100_000.0,
                bv_cvar=100_000.0,
                loss_var=0.0,
                loss_cvar=0.0,
                risk_ratio=0.0,
            )
        )
        assert metrics.risk_ratio == 0.0
        assert metrics.loss_var == 0.0

    def test_serialization_roundtrip_preserves_all_fields(self) -> None:
        original = FeatureRankingMetrics(**_valid_kwargs())
        dumped = original.model_dump()
        restored = FeatureRankingMetrics(**dumped)
        assert restored == original

    def test_equality_on_same_values(self) -> None:
        a = FeatureRankingMetrics(**_valid_kwargs())
        b = FeatureRankingMetrics(**_valid_kwargs())
        assert a == b

    def test_inequality_on_different_values(self) -> None:
        a = FeatureRankingMetrics(**_valid_kwargs(feature_name="A"))
        b = FeatureRankingMetrics(**_valid_kwargs(feature_name="B"))
        assert a != b

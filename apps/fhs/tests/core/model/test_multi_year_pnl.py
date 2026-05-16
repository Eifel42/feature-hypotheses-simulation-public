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

"""Tests for multi-year P&L value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import (
    MultiYearLayer,
    MultiYearPnLMeta,
    MultiYearPnLResult,
    MultiYearRiskProbabilities,
    RiskLayerStats,
)


def _layer() -> MultiYearLayer:
    return MultiYearLayer(
        years=(),
        total_3y=RiskLayerStats(expected=0.0, var_95=0.0, cvar_95=0.0, std=0.0),
        npv=RiskLayerStats(expected=0.0, var_95=0.0, cvar_95=0.0, std=0.0),
    )


def test_multi_year_pnl_result_is_immutable() -> None:
    result = MultiYearPnLResult(
        investment=140_000.0,
        discount_rate=0.08,
        base=_layer(),
        risk1=_layer(),
        risk2=_layer(),
        component=_layer(),
        risk3=_layer(),
        meta=MultiYearPnLMeta(
            selected=("H1",),
            years=3,
            probabilities=MultiYearRiskProbabilities(
                risk_2=0.2,
                risk_3=0.05,
                component_portfolio=0.1,
            ),
            delivery_hit_pct={"H1": 0.2},
            market_hit_pct_by_year=(0.2, 0.19, 0.21),
            global_hit_pct_by_year=(0.05, 0.04, 0.06),
            cluster_hit_pct_by_year=({"A": 0.1}, {"A": 0.11}, {"A": 0.09}),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        result.investment = 120_000.0


def test_multi_year_pnl_result_fields() -> None:
    result = MultiYearPnLResult(
        investment=140_000.0,
        discount_rate=0.08,
        base=_layer(),
        risk1=_layer(),
        risk2=_layer(),
        component=_layer(),
        risk3=_layer(),
        meta=MultiYearPnLMeta(
            selected=("H1",),
            years=3,
            probabilities=MultiYearRiskProbabilities(
                risk_2=0.2,
                risk_3=0.05,
                component_portfolio=0.1,
            ),
            delivery_hit_pct={"H1": 0.2},
            market_hit_pct_by_year=(0.2, 0.19, 0.21),
            global_hit_pct_by_year=(0.05, 0.04, 0.06),
            cluster_hit_pct_by_year=({"A": 0.1}, {"A": 0.11}, {"A": 0.09}),
        ),
    )

    assert result.investment == 140_000.0
    assert result.meta.probabilities.risk_2 == pytest.approx(0.2)
    assert result.discount_rate == pytest.approx(0.08)

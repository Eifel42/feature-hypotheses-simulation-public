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

"""Tests for sensitivity value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import (
    FeatureSensitivityResult,
    PortfolioSensitivityRow,
    SensitivityDetail,
    SensitivityDriver,
    TornadoRow,
)


def test_sensitivity_detail_is_immutable() -> None:
    detail = SensitivityDetail(
        feature="Feature A",
        factor="Risk 1 probability",
        low_probability=0.1,
        base_probability=0.2,
        high_probability=0.3,
        floor_low=90_000.0,
        floor_base=80_000.0,
        floor_high=70_000.0,
        high_vs_base_pct=-12.5,
    )
    with pytest.raises(FrozenInstanceError):
        detail.factor = "Risk 2 probability"


def test_feature_sensitivity_result_construction() -> None:
    result = FeatureSensitivityResult(
        details=(
            SensitivityDetail(
                feature="Feature A",
                factor="Risk 1 probability",
                low_probability=0.1,
                base_probability=0.2,
                high_probability=0.3,
                floor_low=90_000.0,
                floor_base=80_000.0,
                floor_high=70_000.0,
                high_vs_base_pct=-12.5,
            ),
        ),
        drivers=(
            SensitivityDriver(
                feature="Feature A",
                most_sensitive_driver="Risk 1 probability",
                floor_change_eur=-10_000.0,
            ),
        ),
    )
    assert result.details[0].feature == "Feature A"
    assert result.drivers[0].floor_change_eur == -10_000.0


def test_portfolio_sensitivity_row_fields() -> None:
    row = PortfolioSensitivityRow(
        risk_2_probability=0.2,
        risk_3_probability=0.05,
        expected=100_000.0,
        var_95=60_000.0,
        cvar_95=50_000.0,
    )
    assert row.risk_2_probability == 0.2
    assert row.cvar_95 <= row.var_95


def test_feature_sensitivity_result_tornado_summary_orders_by_impact() -> None:
    result = FeatureSensitivityResult(
        details=(
            SensitivityDetail(
                feature="Feature A",
                factor="Risk 1 probability",
                low_probability=0.1,
                base_probability=0.2,
                high_probability=0.3,
                floor_low=95_000.0,
                floor_base=90_000.0,
                floor_high=78_000.0,
                high_vs_base_pct=-13.3,
            ),
            SensitivityDetail(
                feature="Feature B",
                factor="Risk 1 probability",
                low_probability=0.2,
                base_probability=0.3,
                high_probability=0.45,
                floor_low=88_000.0,
                floor_base=82_000.0,
                floor_high=71_000.0,
                high_vs_base_pct=-13.4,
            ),
            SensitivityDetail(
                feature="Feature A",
                factor="Risk 3 probability",
                low_probability=0.025,
                base_probability=0.05,
                high_probability=0.075,
                floor_low=91_000.0,
                floor_base=90_000.0,
                floor_high=86_000.0,
                high_vs_base_pct=-4.4,
            ),
        ),
        drivers=(
            SensitivityDriver(
                feature="Feature A",
                most_sensitive_driver="Risk 1 probability",
                floor_change_eur=-12_000.0,
            ),
        ),
    )

    tornado = result.tornado_summary()
    assert all(isinstance(row, TornadoRow) for row in tornado)
    assert tornado[0].factor == "Risk 1 probability"
    assert tornado[0].avg_floor_change_eur == pytest.approx(-11_500.0)
    assert tornado[0].worst_feature == "Feature A"

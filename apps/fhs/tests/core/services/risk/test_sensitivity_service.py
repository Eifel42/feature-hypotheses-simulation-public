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

"""Tests for SensitivityAnalysisService."""

from fhs.core.model.value_objects import (
    PortfolioSensitivityRow,
    SensitivityDetail,
)
from fhs.core.services.risk.sensitivity import SensitivityAnalysisService


def test_analyze_features_derives_drivers_when_missing() -> None:
    details = (
        SensitivityDetail(
            feature="H1",
            factor="Risk 1 probability",
            low_probability=0.10,
            base_probability=0.20,
            high_probability=0.30,
            floor_low=100_000.0,
            floor_base=90_000.0,
            floor_high=75_000.0,
            high_vs_base_pct=-16.7,
        ),
        SensitivityDetail(
            feature="H1",
            factor="Risk 3 probability",
            low_probability=0.03,
            base_probability=0.05,
            high_probability=0.08,
            floor_low=92_000.0,
            floor_base=90_000.0,
            floor_high=86_000.0,
            high_vs_base_pct=-4.4,
        ),
    )

    result = SensitivityAnalysisService.analyze_features(details)

    assert len(result.drivers) == 1
    assert result.drivers[0].most_sensitive_driver == "Risk 1 probability"


def test_analyze_portfolio_returns_sorted_matrix() -> None:
    rows = [
        PortfolioSensitivityRow(
            risk_2_probability=0.30,
            risk_3_probability=0.05,
            expected=100_000.0,
            var_95=75_000.0,
            cvar_95=68_000.0,
        ),
        PortfolioSensitivityRow(
            risk_2_probability=0.20,
            risk_3_probability=0.03,
            expected=110_000.0,
            var_95=82_000.0,
            cvar_95=74_000.0,
        ),
    ]

    sorted_rows = SensitivityAnalysisService.analyze_portfolio(rows)

    assert sorted_rows[0].risk_2_probability == 0.20
    assert sorted_rows[1].risk_2_probability == 0.30

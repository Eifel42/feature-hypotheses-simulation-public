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

"""Tests for MultiYearResult and YearResult value objects."""

from __future__ import annotations

import numpy as np

from fhs.core.model.value_objects.multi_year_result import YearResult


class TestYearResult:
    """Tests for YearResult value object."""

    def test_spread_pct_with_positive_expected(self):
        """Spread percentage is calculated correctly."""
        result = YearResult(
            year=1,
            scenarios=np.array([100, 200, 300]),
            expected=200.0,
            var_95=100.0,
            cvar_95=80.0,
            p95=300.0,
            std=10.0,
        )
        # spread_pct = (p95 - var_95) / expected * 100
        # = (300 - 100) / 200 * 100 = 100.0
        assert result.spread_pct == 100.0

    def test_spread_pct_with_zero_expected(self):
        """Spread percentage returns 0 when expected is 0."""
        result = YearResult(
            year=1,
            scenarios=np.array([0, 0, 0]),
            expected=0.0,
            var_95=0.0,
            cvar_95=0.0,
            p95=0.0,
            std=0.0,
        )
        assert result.spread_pct == 0.0

    def test_from_scenarios_empty_array(self):
        """from_scenarios with empty array returns zeros."""
        result = YearResult.from_scenarios(year=1, scenarios=np.array([]))
        assert result.year == 1
        assert len(result.scenarios) == 0
        assert result.expected == 0.0
        assert result.var_95 == 0.0
        assert result.cvar_95 == 0.0
        assert result.p95 == 0.0
        assert result.std == 0.0

    def test_from_scenarios_with_data(self):
        """from_scenarios calculates statistics correctly."""
        scenarios = np.array([10, 20, 30, 40, 50])
        result = YearResult.from_scenarios(year=2, scenarios=scenarios)
        assert result.year == 2
        assert result.expected == 30.0
        assert result.var_95 > 0
        assert result.p95 > 0

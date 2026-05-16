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

"""Tests for PortfolioSnapshot value object."""

from __future__ import annotations

from fhs.core.model.value_objects.portfolio_snapshot import PortfolioSnapshot


class TestPortfolioSnapshot:
    """Tests for PortfolioSnapshot value object."""

    def test_safety_buffer(self):
        """Safety buffer is VaR - investment."""
        snapshot = PortfolioSnapshot(
            expected=150_000.0,
            var_95=80_000.0,
            cvar_95=70_000.0,
            std_dev=20_000.0,
            investment=100_000.0,
        )
        assert snapshot.safety_buffer == -20_000.0

    def test_roi_positive_investment(self):
        """ROI is calculated correctly."""
        snapshot = PortfolioSnapshot(
            expected=150_000.0,
            var_95=80_000.0,
            cvar_95=70_000.0,
            std_dev=20_000.0,
            investment=100_000.0,
        )
        # roi = (expected - investment) / investment
        # = (150_000 - 100_000) / 100_000 = 0.5
        assert snapshot.roi == 0.5

    def test_roi_zero_investment(self):
        """ROI returns 0 when investment is 0."""
        snapshot = PortfolioSnapshot(
            expected=150_000.0,
            var_95=80_000.0,
            cvar_95=70_000.0,
            std_dev=20_000.0,
            investment=0.0,
        )
        assert snapshot.roi == 0.0

    def test_roi_negative_investment(self):
        """ROI returns 0 when investment is negative."""
        snapshot = PortfolioSnapshot(
            expected=150_000.0,
            var_95=80_000.0,
            cvar_95=70_000.0,
            std_dev=20_000.0,
            investment=-10_000.0,
        )
        assert snapshot.roi == 0.0

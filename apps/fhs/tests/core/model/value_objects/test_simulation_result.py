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

"""Tests for SimulationResult value object - missing coverage."""

from __future__ import annotations

import numpy as np

from fhs.core.model.value_objects.simulation_result import SimulationResult


class TestSimulationResultCoverage:
    """Cover the missing line 128 (loss_var_95 property)."""

    def test_loss_var_95(self):
        """loss_var_95 property is calculated correctly."""
        results = np.array([100, 200, 300])
        result = SimulationResult(
            feature_name="Test Feature",
            results=results,
            expected_value=200.0,
        )
        # loss_var_95 = expected_value - var_95
        # var_95 should be the 5th percentile
        expected_var_95 = float(np.percentile(results, 5))
        expected_loss_var = 200.0 - expected_var_95
        assert abs(result.loss_var_95 - expected_loss_var) < 0.01

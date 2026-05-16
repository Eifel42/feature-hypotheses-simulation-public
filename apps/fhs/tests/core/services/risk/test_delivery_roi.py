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

"""Tests for DeliveryRiskService.risk_management_assessment with missing scenario labels."""

from fhs.core.model.value_objects import DeliveryStressResult
from fhs.core.services.risk.delivery import DeliveryRiskService


def test_risk_management_assessment_returns_zero_metrics_when_baseline_missing():
    """Test that risk_management_assessment returns zero metrics when baseline scenario is missing."""
    scenarios = {
        "Managed": DeliveryStressResult(
            prob_success=0.9,
            prob_failure=0.1,
            expected_delay_weeks=1.0,
            expected_impact_eur=10000.0,
            impact_var_95_eur=5000.0,
            impact_cvar_95_eur=3000.0,
        )
    }

    roi = DeliveryRiskService.risk_management_assessment(
        scenarios=scenarios,
        investment=100000.0,
        baseline_label="Baseline",  # not in scenarios
        managed_label="Managed",
    )

    assert roi.program_cost_eur == 0.0
    assert roi.avoided_expected_loss_eur == 0.0
    assert roi.net_expected_benefit_eur == 0.0
    assert roi.tail_risk_reduction_var_95_eur == 0.0


def test_risk_management_assessment_returns_zero_metrics_when_managed_missing():
    """Test that risk_management_assessment returns zero metrics when managed scenario is missing."""
    scenarios = {
        "Baseline": DeliveryStressResult(
            prob_success=0.8,
            prob_failure=0.2,
            expected_delay_weeks=2.0,
            expected_impact_eur=20000.0,
            impact_var_95_eur=15000.0,
            impact_cvar_95_eur=12000.0,
        )
    }

    roi = DeliveryRiskService.risk_management_assessment(
        scenarios=scenarios,
        investment=100000.0,
        baseline_label="Baseline",
        managed_label="Managed",  # not in scenarios
    )

    assert roi.program_cost_eur == 0.0
    assert roi.avoided_expected_loss_eur == 0.0
    assert roi.net_expected_benefit_eur == 0.0
    assert roi.tail_risk_reduction_var_95_eur == 0.0

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

"""Tests for component risk value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import ClusterRisk, ComponentRiskResult


def test_cluster_risk_is_immutable() -> None:
    cluster = ClusterRisk(
        cluster="Traceability Platform",
        features=("H2", "H3"),
        configured_probability=0.12,
        simulated_probability=0.118,
        expected_incremental_loss_eur=21_000.0,
        var_incremental_loss_eur=35_000.0,
        cvar_incremental_loss_eur=44_000.0,
    )

    with pytest.raises(FrozenInstanceError):
        cluster.cluster = "Other"


def test_component_risk_result_fields() -> None:
    result = ComponentRiskResult(
        confidence=0.95,
        selected=("H1", "H2", "H3"),
        cluster_risks=(
            ClusterRisk(
                cluster="Traceability Platform",
                features=("H2", "H3"),
                configured_probability=0.12,
                simulated_probability=0.118,
                expected_incremental_loss_eur=21_000.0,
                var_incremental_loss_eur=35_000.0,
                cvar_incremental_loss_eur=44_000.0,
            ),
        ),
        portfolio_component_probability=0.21,
        portfolio_component_probability_analytical=0.22,
        portfolio_component_probability_ci95=(0.19, 0.23),
        portfolio_expected_incremental_loss_eur=28_000.0,
        portfolio_var_incremental_loss_eur=42_000.0,
        portfolio_cvar_incremental_loss_eur=50_000.0,
    )

    assert result.cluster_risks[0].cluster == "Traceability Platform"
    assert result.portfolio_component_probability == pytest.approx(0.21)

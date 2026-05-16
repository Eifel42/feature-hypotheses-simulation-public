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

"""Tests for ComponentRiskService."""

import numpy as np
import pytest

from fhs.core.model.value_objects import ComponentRiskResult
from fhs.core.services.risk.component_risk import ComponentRiskService


def test_simulate_returns_typed_component_risk_result() -> None:
    payload = {
        "Cluster A": {
            "features": ("H1",),
            "configured_probability": 0.08,
            "simulated_probability": 0.09,
            "expected_incremental_loss_eur": 11_000.0,
            "var_incremental_loss_eur": 20_000.0,
            "cvar_incremental_loss_eur": 24_000.0,
        },
        "Cluster B": {
            "features": ("H2", "H3"),
            "configured_probability": 0.12,
            "simulated_probability": 0.11,
            "expected_incremental_loss_eur": 15_000.0,
            "var_incremental_loss_eur": 26_000.0,
            "cvar_incremental_loss_eur": 31_000.0,
        },
    }

    result = ComponentRiskService.simulate(
        selected=("H1", "H2", "H3"),
        cluster_payload=payload,
        confidence=0.95,
    )

    assert isinstance(result, ComponentRiskResult)
    assert len(result.cluster_risks) == 2
    assert result.portfolio_expected_incremental_loss_eur == pytest.approx(26_000.0)


def test_summary_exposes_core_metrics() -> None:
    payload = {
        "Cluster A": {
            "configured_probability": 0.10,
            "simulated_probability": 0.12,
            "expected_incremental_loss_eur": 8_000.0,
            "var_incremental_loss_eur": 14_000.0,
            "cvar_incremental_loss_eur": 18_000.0,
        }
    }
    result = ComponentRiskService.simulate(
        selected=("H1",),
        cluster_payload=payload,
    )
    summary = ComponentRiskService.summary(result)

    assert summary["clusters_at_risk"] == 1.0
    assert summary["portfolio_var_incremental_loss_eur"] == pytest.approx(14_000.0)


def test_simulated_from_distributions_returns_expected_probabilities() -> None:
    cluster_hits = {
        "Cluster A": np.array([True, False, False, True], dtype=bool),
        "Cluster B": np.array([False, False, True, False], dtype=bool),
    }
    result = ComponentRiskService.simulated_from_distributions(
        selected=("H1", "H2"),
        cluster_hits=cluster_hits,
        cluster_probabilities={"Cluster A": 0.5, "Cluster B": 0.25},
        cluster_features={"Cluster A": ("H1",), "Cluster B": ("H2",)},
        incremental_losses=np.array([0.0, 5.0, 20.0, 10.0]),
        cluster_incremental_losses={
            "Cluster A": np.array([0.0, 0.0, 0.0, 10.0]),
            "Cluster B": np.array([0.0, 5.0, 20.0, 0.0]),
        },
        confidence=0.95,
    )

    assert isinstance(result, ComponentRiskResult)
    assert result.portfolio_component_probability == pytest.approx(0.75)
    assert result.portfolio_component_probability_analytical == pytest.approx(0.625)
    assert result.portfolio_expected_incremental_loss_eur == pytest.approx(8.75)


def test_analytical_from_cluster_estimates_aggregates_losses() -> None:
    result = ComponentRiskService.analytical_from_cluster_estimates(
        selected=("H1", "H2"),
        cluster_features={"Cluster A": ("H1",), "Cluster B": ("H2",)},
        cluster_probabilities={"Cluster A": 0.1, "Cluster B": 0.2},
        expected_losses={"Cluster A": 1_000.0, "Cluster B": 2_500.0},
        var_losses={"Cluster A": 2_000.0, "Cluster B": 4_000.0},
        cvar_losses={"Cluster A": 2_300.0, "Cluster B": 4_800.0},
        confidence=0.95,
    )

    assert isinstance(result, ComponentRiskResult)
    assert result.portfolio_component_probability == pytest.approx(0.28)
    assert result.portfolio_expected_incremental_loss_eur == pytest.approx(3_500.0)
    assert result.portfolio_var_incremental_loss_eur == pytest.approx(6_000.0)
    assert result.portfolio_cvar_incremental_loss_eur == pytest.approx(7_100.0)


def test_simulated_from_component_pnl_function_builds_counterfactual_losses() -> None:
    full_pnl = np.array([100.0, 80.0, 50.0, 90.0], dtype=float)
    no_component_pnl = np.array([100.0, 90.0, 70.0, 90.0], dtype=float)
    pnl_without_cluster_a = np.array([100.0, 80.0, 70.0, 90.0], dtype=float)
    pnl_without_cluster_b = np.array([100.0, 90.0, 50.0, 90.0], dtype=float)

    pnl_by_key = {
        (True, None): full_pnl,
        (False, None): no_component_pnl,
        (True, frozenset({"Cluster B"})): pnl_without_cluster_a,
        (True, frozenset({"Cluster A"})): pnl_without_cluster_b,
    }
    calls: list[tuple[bool, frozenset[str] | None]] = []

    def pnl_function(
        include_component: bool,
        enabled_clusters: set[str] | None,
    ) -> np.ndarray:
        key = (
            include_component,
            None if enabled_clusters is None else frozenset(enabled_clusters),
        )
        calls.append(key)
        return pnl_by_key[key]

    result = ComponentRiskService.simulated_from_component_pnl_function(
        selected=("F1: H1", "F2: H2"),
        cluster_hits={
            "Cluster A": np.array([False, False, True, False], dtype=bool),
            "Cluster B": np.array([False, True, False, False], dtype=bool),
        },
        cluster_probabilities={"Cluster A": 0.5, "Cluster B": 0.25},
        feature_cluster_by_name={"F1: H1": "Cluster A", "F2: H2": "Cluster B"},
        pnl_function=pnl_function,
        confidence=0.95,
    )

    assert set(calls) == {
        (True, None),
        (False, None),
        (True, frozenset({"Cluster A"})),
        (True, frozenset({"Cluster B"})),
    }
    assert result.portfolio_component_probability == pytest.approx(0.5)
    assert result.portfolio_component_probability_analytical == pytest.approx(0.625)
    assert result.portfolio_expected_incremental_loss_eur == pytest.approx(7.5)

    clusters = {risk.cluster: risk for risk in result.cluster_risks}
    assert clusters["Cluster A"].features == ("H1",)
    assert clusters["Cluster B"].features == ("H2",)
    assert clusters["Cluster A"].expected_incremental_loss_eur == pytest.approx(5.0)
    assert clusters["Cluster B"].expected_incremental_loss_eur == pytest.approx(2.5)


def test_analytical_from_cluster_business_value_function_aggregates_callback_values() -> (
    None
):
    calls: list[tuple[str, tuple[str, ...]]] = []

    def cluster_business_value(
        cluster: str,
        feat_names: tuple[str, ...],
    ) -> tuple[float, float]:
        calls.append((cluster, feat_names))
        if cluster == "Cluster A":
            return 3_000.0, 2_500.0
        return 1_000.0, 800.0

    result = ComponentRiskService.analytical_from_cluster_business_value_function(
        selected=("F1: H1", "F2: H2", "F3: H3"),
        feature_cluster_by_name={
            "F1: H1": "Cluster A",
            "F2: H2": "Cluster A",
            "F3: H3": "Cluster B",
        },
        cluster_probabilities={"Cluster A": 0.1, "Cluster B": 0.2},
        cluster_business_value_function=cluster_business_value,
        expected_loss_multiplier=0.6,
        confidence=0.95,
    )

    assert isinstance(result, ComponentRiskResult)
    assert calls == [
        ("Cluster A", ("F1: H1", "F2: H2")),
        ("Cluster B", ("F3: H3",)),
    ]
    assert result.portfolio_component_probability == pytest.approx(0.28)
    assert result.portfolio_expected_incremental_loss_eur == pytest.approx(300.0)
    assert result.portfolio_var_incremental_loss_eur == pytest.approx(410.0)
    assert result.portfolio_cvar_incremental_loss_eur == pytest.approx(410.0)

    clusters = {risk.cluster: risk for risk in result.cluster_risks}
    assert clusters["Cluster A"].features == ("H1", "H2")
    assert clusters["Cluster B"].features == ("H3",)


# ---------------------------------------------------------------------------
# Validation / edge-case tests for missing coverage branches
# ---------------------------------------------------------------------------


def test_simulated_from_distributions_raises_on_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        ComponentRiskService.simulated_from_distributions(
            selected=("H1",),
            cluster_hits={"C": np.array([True], dtype=bool)},
            cluster_probabilities={"C": 0.1},
            cluster_features={"C": ("H1",)},
            incremental_losses=np.array([10.0]),
            cluster_incremental_losses={"C": np.array([10.0])},
            confidence=1.5,
        )


def test_simulated_from_distributions_empty_selected_returns_zero_result() -> None:
    result = ComponentRiskService.simulated_from_distributions(
        selected=(),
        cluster_hits={},
        cluster_probabilities={},
        cluster_features={},
        incremental_losses=np.array([10.0]),
        cluster_incremental_losses={},
        confidence=0.95,
    )
    assert result.selected == ()
    assert result.portfolio_expected_incremental_loss_eur == 0.0


def test_simulated_from_distributions_empty_incremental_losses_returns_zero_result() -> (
    None
):
    result = ComponentRiskService.simulated_from_distributions(
        selected=("H1",),
        cluster_hits={"C": np.array([], dtype=bool)},
        cluster_probabilities={"C": 0.1},
        cluster_features={"C": ("H1",)},
        incremental_losses=np.array([], dtype=float),
        cluster_incremental_losses={"C": np.array([], dtype=float)},
        confidence=0.95,
    )
    assert result.portfolio_expected_incremental_loss_eur == 0.0
    assert result.portfolio_var_incremental_loss_eur == 0.0


def test_simulated_from_distributions_cluster_with_empty_losses_hits_zero_branch() -> (
    None
):
    """Cover lines 197-199: cluster loop with non-empty incremental_losses but empty per-cluster losses."""
    result = ComponentRiskService.simulated_from_distributions(
        selected=("H1",),
        cluster_hits={"C": np.array([True, False, True], dtype=bool)},
        cluster_probabilities={"C": 0.1},
        cluster_features={"C": ("H1",)},
        incremental_losses=np.array([10.0, 20.0, 30.0], dtype=float),
        cluster_incremental_losses={"C": np.array([], dtype=float)},
        confidence=0.95,
    )
    assert result.cluster_risks[0].var_incremental_loss_eur == 0.0
    assert result.cluster_risks[0].cvar_incremental_loss_eur == 0.0
    assert result.cluster_risks[0].expected_incremental_loss_eur == 0.0


def test_analytical_from_cluster_business_value_function_empty_selected_returns_zero() -> (
    None
):
    """Cover line 321: empty selected in analytical_from_cluster_business_value_function."""
    result = ComponentRiskService.analytical_from_cluster_business_value_function(
        selected=(),
        feature_cluster_by_name={},
        cluster_probabilities={},
        cluster_business_value_function=lambda c, n: (0.0, 0.0),
        confidence=0.95,
    )
    assert result.selected == ()
    assert result.portfolio_expected_incremental_loss_eur == 0.0


def test_analytical_from_cluster_estimates_empty_selected_returns_zero() -> None:
    """Cover line 386: empty selected in analytical_from_cluster_estimates."""
    result = ComponentRiskService.analytical_from_cluster_estimates(
        selected=(),
        cluster_features={},
        cluster_probabilities={},
        expected_losses={},
        var_losses={},
        cvar_losses={},
        confidence=0.95,
    )
    assert result.selected == ()
    assert result.portfolio_expected_incremental_loss_eur == 0.0


def test_analytical_from_cluster_business_value_function_raises_on_invalid_confidence() -> (
    None
):
    with pytest.raises(ValueError):
        ComponentRiskService.analytical_from_cluster_business_value_function(
            selected=("H1",),
            feature_cluster_by_name={"H1": "C"},
            cluster_probabilities={"C": 0.1},
            cluster_business_value_function=lambda c, n: (100.0, 80.0),
            confidence=0.0,
        )


def test_analytical_from_cluster_estimates_raises_on_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        ComponentRiskService.analytical_from_cluster_estimates(
            selected=("H1",),
            cluster_features={"C": ("H1",)},
            cluster_probabilities={"C": 0.1},
            expected_losses={"C": 10.0},
            var_losses={"C": 15.0},
            cvar_losses={"C": 15.0},
            confidence=2.0,
        )

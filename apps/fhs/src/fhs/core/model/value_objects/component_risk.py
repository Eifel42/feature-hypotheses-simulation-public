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

"""Component risk value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterRisk:
    """Risk detail for one dependency cluster with counterfactual analysis."""

    cluster: str
    features: tuple[str, ...]
    configured_probability: float
    simulated_probability: float
    expected_incremental_loss_eur: float
    var_incremental_loss_eur: float
    cvar_incremental_loss_eur: float


@dataclass(frozen=True)
class ComponentRiskResult:
    """Simulated component/cluster risk for a portfolio."""

    confidence: float
    selected: tuple[str, ...]
    cluster_risks: tuple[ClusterRisk, ...]
    portfolio_component_probability: float
    portfolio_component_probability_analytical: float
    portfolio_component_probability_ci95: tuple[float, float]
    portfolio_expected_incremental_loss_eur: float
    portfolio_var_incremental_loss_eur: float
    portfolio_cvar_incremental_loss_eur: float

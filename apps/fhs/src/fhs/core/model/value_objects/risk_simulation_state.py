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

"""Internal risk simulation state value object."""

from dataclasses import dataclass

import numpy as np

from ..config.scenario import ScenarioRiskModel


@dataclass(frozen=True)
class RiskSimulationState:
    """Internal state bag for portfolio year-1 risk simulation."""

    selected: tuple[str, ...]
    risk_model: ScenarioRiskModel
    rng: np.random.Generator
    delivery_gates: dict[str, np.ndarray]
    market_hits: np.ndarray
    global_hits: np.ndarray
    cluster_hits: dict[str, np.ndarray]
    base_scenarios: dict[str, np.ndarray]
    p2: float
    p3: float
    cluster_probabilities: dict[str, float]
    n_scenarios: int

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

"""Case-study specific value objects used by application services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..entities import Feature

from .simulation_result import SimulationResult


@dataclass(frozen=True)
class FeatureYear1Result:
    """Typed year-1 simulation result for one feature."""

    key: str
    feature: Feature
    result: SimulationResult
    scenarios_eur: np.ndarray
    expected_eur: float
    var_95_eur: float
    cvar_95_eur: float
    p95_eur: float
    std_eur: float
    roi: float

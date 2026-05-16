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

"""Portfolio context protocol for explicit collaborator dependencies."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

import numpy as np

from fhs.core.model import Feature, SimulationResult


class PortfolioContext(Protocol):
    """Explicit interface between portfolio facade and collaborators.

    This protocol defines the contract that collaborators can depend on,
    ensuring type safety and explicit API boundaries.
    """

    @property
    def features(self) -> list[Feature]:
        """All features in the portfolio."""
        ...

    @property
    def simulation_results(self) -> dict[str, SimulationResult]:
        """Cached simulation results for all features."""
        ...

    @property
    def budget(self) -> float:
        """Total budget for portfolio optimization."""
        ...

    @property
    def discount_rate(self) -> float:
        """Discount rate for NPV calculations."""
        ...

    @property
    def seed(self) -> int:
        """Random seed for reproducibility."""
        ...

    @property
    def scenarios(self) -> int:
        """Number of Monte Carlo scenarios."""
        ...

    def resolve_names(self, names: Iterable[str] | None) -> list[str]:
        """Resolve feature names, defaulting to all features if None.

        Args:
            names: Feature names to resolve, or None for all features.

        Returns:
            List of resolved feature names that exist in the portfolio.
        """
        ...

    def get_feature(self, name: str) -> Feature:
        """Get feature by name.

        Args:
            name: Feature name.

        Returns:
            Feature instance.

        Raises:
            KeyError: If feature name does not exist.
        """
        ...

    def subset_results(
        self,
        names: Iterable[str] | None = None,
    ) -> dict[str, SimulationResult]:
        """Get simulation results for selected feature names.

        Args:
            names: Feature names to include, or None for all features.

        Returns:
            Dictionary mapping feature names to simulation results.
        """
        ...

    def sum_portfolio_scenarios(
        self,
        simulation_subset: dict[str, SimulationResult],
    ) -> np.ndarray:
        """Sum business value scenarios across multiple features.

        Args:
            simulation_subset: Simulation results to aggregate.

        Returns:
            Array of portfolio business value scenarios (EUR).
        """
        ...

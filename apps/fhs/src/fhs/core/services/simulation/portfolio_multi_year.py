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

"""Portfolio multi-year aggregation service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from fhs.core.model import Feature, MultiYearResult, YearResult
from fhs.core.services.simulation.simulator import FeatureSimulator


class PortfolioMultiYearService:
    """Build multi-year portfolio results from feature simulations."""

    @staticmethod
    def simulate(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        years: int,
        scenarios: int,
        discount_rate: float,
        seed: int,
        feature_name: str = "Selected Portfolio",
    ) -> MultiYearResult:
        """Combined multi-year simulation for selected features."""
        resolved = [name for name in selected if name in feature_by_name]
        rate = float(discount_rate)
        if not resolved:
            return MultiYearResult(
                feature_name="Empty Portfolio",
                years=[],
                discount_rate=rate,
            )

        simulated = [
            FeatureSimulator(seed=seed + idx).simulate_feature_multi_year(
                feature_by_name[name],
                years=years,
                scenarios=scenarios,
                discount_rate=rate,
            )
            for idx, name in enumerate(resolved)
        ]

        combined_years: list[YearResult] = []
        for idx in range(years):
            year_scenarios = np.sum(
                [result.years[idx].scenarios for result in simulated],
                axis=0,
            )
            combined_years.append(
                YearResult.from_scenarios(year=idx + 1, scenarios=year_scenarios)
            )

        return MultiYearResult(
            feature_name=feature_name,
            years=combined_years,
            discount_rate=rate,
        )

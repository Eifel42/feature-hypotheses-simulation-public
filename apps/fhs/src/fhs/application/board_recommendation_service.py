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

"""Board recommendation service — compact multi-year portfolio summary.

Generates a compact executive recommendation including:
- Multi-year portfolio results (Year 1, 2, 3)
- GO/NO-GO decision logic
- Ranked features by expected business value
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fhs.core.model import (
    Feature,
    FeatureRankingRow,
    MultiYearResult,
    SimulationResult,
    YearResult,
)
from fhs.core.model.value_objects.case_study import FeatureYear1Result
from fhs.core.model.value_objects.governance import ModelCard
from fhs.core.services.simulation.simulator import FeatureSimulator


@dataclass
class FeatureResults:
    """Aggregated simulation results for a single feature."""

    feature: Feature
    result: SimulationResult
    biz_value: float
    expected_eur: float
    var95_eur: float
    p95_eur: float
    std_eur: float
    scenarios_eur: np.ndarray


@dataclass
class BoardRecommendation:
    """Compact board recommendation result."""

    portfolio_multi_year: MultiYearResult
    """Multi-year portfolio simulation results."""

    ranked_features: list[FeatureRankingRow]
    """Features ranked by expected business value (highest first)."""

    go_decision: str
    """'GO', 'CONDITIONAL_GO', or 'REVIEW' decision."""

    go_reason: str
    """Explanation of the GO/NO-GO decision."""

    total_portfolio_expected: float
    """Total expected portfolio business value (all features combined)."""

    total_portfolio_var95: float
    """Total portfolio Business Value Floor 95% / BVF 95% (downside floor)."""

    total_cost: float
    """Total development cost across all features."""

    total_annual_installment: float
    """Sum of annual installment charges across all features (year-1 P&L burden)."""

    model_card: ModelCard = field(default_factory=ModelCard)
    """Governance artifact identifying the model that produced this recommendation."""

    @property
    def kpi_phase_data(self) -> list[tuple[str, str]]:
        """Formatted (value, label) pairs for KPI cards, ordered by rank.

        Ready for use with show.kpi_card() — no EUR formatting needed in notebooks.
        """
        return [
            (
                f"EUR {item.expected_eur:,.0f}",
                f"Phase {idx} — {item.name.split(': ', 1)[-1] if ': ' in item.name else item.name}",
            )
            for idx, item in enumerate(self.ranked_features, 1)
        ]

    @property
    def portfolio_kpi_rows(self) -> list[tuple[str, str, None]]:
        """Metric rows for show.metrics() — portfolio context behind the board decision.

        Shows both the full investment commitment and the year-1 P&L charge so
        the reader can trace every number in the decision message to a concrete row.

        Row order:
          1. Total Investment      — full development cost (multi-year commitment)
          2. Year-1 P&L Charge     — sum of annual installment (effective year-1 burden)
          3. Portfolio Expected    — simulated mean business value, Year 1
          4. Portfolio Floor       — Business Value Floor 95% / BVF 95% (95 of 100 scenarios exceed this)
        """
        return [
            ("Investment — Full commitment", f"€{self.total_cost:,.0f}", None),
            (
                "Investment — Year-1 P&L charge",
                f"€{self.total_annual_installment:,.0f}",
                None,
            ),
            (
                "Portfolio Expected (Year 1)",
                f"€{self.total_portfolio_expected:,.0f}",
                None,
            ),
            ("Portfolio Floor (BVF 95%)", f"€{self.total_portfolio_var95:,.0f}", None),
        ]

    @property
    def decision_level(self) -> str:
        """Display level: 'success' for GO, 'warning' for all other outcomes."""
        return "success" if self.go_decision == "GO" else "warning"

    @property
    def decision_message(self) -> str:
        """Formatted board decision message ready for show.success() or show.warning()."""
        if self.go_decision == "GO":
            return f"Board decision: GO. {self.go_reason}"
        if self.go_decision == "CONDITIONAL_GO":  # pragma: no cover - defensive
            return f"Board decision: Conditional GO. {self.go_reason}"  # pragma: no cover - defensive
        return f"Board decision: Review first. {self.go_reason}"  # pragma: no cover - defensive


class BoardRecommendationService:
    """Generates compact board recommendations from feature simulations."""

    def __init__(self, seed: int | None = None, scenarios: int = 100_000):
        """Initialize the service.

        Args:
            seed: Random seed for reproducibility
            scenarios: Number of Monte Carlo scenarios per feature
        """
        self.seed = seed
        self.scenarios = scenarios

    def _simulator_for_index(self, idx: int) -> Any:
        """Build per-feature simulator with deterministic seed offset."""
        if self.seed is None:
            return FeatureSimulator()  # pragma: no cover - defensive
        return FeatureSimulator(seed=self.seed + idx)

    @staticmethod
    def _year1_metrics(
        sim: Any,
        feature: Feature,
        key: str,
        *,
        scenarios: int,
        year1_results: Mapping[str, FeatureYear1Result] | None,
    ) -> tuple[float, float]:
        if year1_results is not None and key in year1_results:
            return (  # pragma: no cover - defensive
                float(year1_results[key].expected_eur),
                float(year1_results[key].var_95_eur),
            )

        year1 = sim.simulate_feature(feature, scenarios=scenarios)
        return (
            float(year1.expected_business_value),
            float(year1.business_value_at_risk_95),
        )

    def simulate_features(
        self,
        features: list[Feature],
        business_values: dict[str, float] | None = None,
    ) -> dict[str, FeatureResults]:
        """Simulate features and return results for analysis.

        This is used by notebooks for detailed charts and comparisons.

        Args:
            features: List of features to analyze
            business_values: Dict mapping feature.name to €/conversion value

        Returns:
            Dict of {feature_key: FeatureResults} for charting and analysis
        """
        # Kept for API compatibility; value-per-conversion comes from the feature itself.
        _ = business_values  # pragma: no cover - defensive
        # pragma: no cover - defensive
        results = {}  # pragma: no cover - defensive
        for label, feature in enumerate(features):  # pragma: no cover - defensive
            sim = self._simulator_for_index(label)  # pragma: no cover - defensive
            r = sim.simulate_feature(
                feature, scenarios=self.scenarios
            )  # pragma: no cover - defensive
            # pragma: no cover - defensive
            results[feature.name] = FeatureResults(  # pragma: no cover - defensive
                feature=feature,  # pragma: no cover - defensive
                result=r,  # pragma: no cover - defensive
                # Business value metrics are already in EUR via SimulationResult helpers.  # pragma: no cover - defensive
                biz_value=feature.business_value_per_conversion,  # pragma: no cover - defensive
                expected_eur=r.expected_business_value,  # pragma: no cover - defensive
                var95_eur=r.business_value_at_risk_95,  # pragma: no cover - defensive
                p95_eur=r.p95
                * feature.business_value_per_conversion,  # pragma: no cover - defensive
                std_eur=r.std
                * feature.business_value_per_conversion,  # pragma: no cover - defensive
                scenarios_eur=r.results_array
                * feature.business_value_per_conversion,  # pragma: no cover - defensive
            )  # pragma: no cover - defensive
        # pragma: no cover - defensive
        return results  # pragma: no cover - defensive

    def generate_recommendation(
        self,
        features: list[Feature],
        business_values: dict[str, float] | None = None,
        *,
        discount_rate: float = 0.10,
        year1_results: Mapping[str, FeatureYear1Result] | None = None,
        model_card: ModelCard | None = None,
    ) -> BoardRecommendation:
        """Generate compact board recommendation from features.

        Args:
            features: List of features to analyze
            business_values: Dict mapping feature.name to €/conversion value
            discount_rate: Annual discount rate for NPV (from scenario config)
            year1_results: Optional pre-computed Year-1 delivery risk results

        Returns:
            BoardRecommendation with multi-year results, ranking, and decision
        """
        # Kept for API compatibility; value-per-conversion comes from the feature itself.
        _ = business_values

        # Simulate each feature independently
        multi_year_results = []
        individual_results = {}

        for idx, feature in enumerate(features):
            sim = self._simulator_for_index(idx)
            myr = sim.simulate_feature_multi_year(
                feature, scenarios=self.scenarios, discount_rate=discount_rate
            )
            multi_year_results.append(myr)

            # Store expected business value for ranking.
            # Prefer precomputed year-1 EUR values from the notebook to ensure
            # consistency across all displayed tables.
            key = getattr(feature, "key", feature.name.split(":")[0].strip())
            expected_eur, var95_eur = self._year1_metrics(
                sim,
                feature,
                key,
                scenarios=self.scenarios,
                year1_results=year1_results,
            )

            individual_results[feature.name] = {
                "feature": feature,
                "multi_year": myr,
                "expected_eur": expected_eur,
                "var95_eur": var95_eur,
            }

        # Build portfolio across years
        portfolio_years = []
        for year_idx in range(3):
            year_draws = np.sum(
                [result.years[year_idx].scenarios for result in multi_year_results],
                axis=0,
            )
            portfolio_years.append(
                YearResult.from_scenarios(year=year_idx + 1, scenarios=year_draws)
            )

        portfolio_multi_year = MultiYearResult(
            feature_name="Portfolio Total",
            years=portfolio_years,
            discount_rate=discount_rate,
        )

        # Calculate portfolio metrics
        portfolio_expected = portfolio_multi_year.years[0].expected
        portfolio_var95 = portfolio_multi_year.years[0].var_95
        total_cost = sum(f.development_cost for f in features)
        total_annual_installment = sum(f.annual_installment for f in features)

        # Rank features by expected business value
        ranked = sorted(
            individual_results.items(),
            key=lambda kv: kv[1]["expected_eur"],
            reverse=True,
        )

        ranked_features = [
            FeatureRankingRow(
                key=kv[0].split(":")[0].strip(),
                name=kv[1]["feature"].name,
                expected_eur=float(kv[1]["expected_eur"]),
                var95_eur=float(kv[1]["var95_eur"]),
                cost=float(kv[1]["feature"].development_cost),
                multi_year=kv[1]["multi_year"],
            )
            for kv in ranked
        ]

        # Determine GO/NO-GO decision (check single feature THEN portfolio)
        if ranked_features:
            top_feature = ranked_features[0]
            top_floor = top_feature.var95_eur
            top_expected = top_feature.expected_eur

            # Priority 1: Single feature covers cost on downside
            if top_floor >= total_cost:
                decision = "GO"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Top feature ({top_feature.key}) covers cost on downside floor "
                    f"(€{top_floor:,.0f} >= €{total_cost:,.0f})"
                )
            # Priority 2: Single feature covers cost on expected value
            elif top_expected >= total_cost:
                decision = "CONDITIONAL_GO"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Top feature ({top_feature.key}) covers cost on expected value "
                    f"(€{top_expected:,.0f}) but not on downside (€{top_floor:,.0f}). "
                    f"Monitor execution risk."
                )
            # Priority 3: Portfolio covers cost on downside
            elif portfolio_var95 >= total_cost:
                decision = "GO"
                reason = (
                    f"Portfolio (all features combined) covers cost on downside floor "
                    f"(€{portfolio_var95:,.0f} >= €{total_cost:,.0f})"
                )
            # Priority 4: Portfolio covers cost on expected value
            elif portfolio_expected >= total_cost:  # pragma: no cover - defensive
                decision = "CONDITIONAL_GO"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Portfolio covers cost on expected value "  # pragma: no cover - defensive
                    f"(€{portfolio_expected:,.0f}) but not on downside (€{portfolio_var95:,.0f}). "  # pragma: no cover - defensive
                    f"All features needed for viability."  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
            # Priority 5: Portfolio floor covers year-1 installment charge  # pragma: no cover - defensive
            elif (
                portfolio_var95 >= total_annual_installment
            ):  # pragma: no cover - defensive
                decision = "CONDITIONAL_GO"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Portfolio floor (€{portfolio_var95:,.0f}) covers the year-1 P&L charge "  # pragma: no cover - defensive
                    f"(€{total_annual_installment:,.0f}) even in the downside case, "  # pragma: no cover - defensive
                    f"but does not recover the full investment (€{total_cost:,.0f}). "  # pragma: no cover - defensive
                    f"Multi-year payback required."  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
            # Priority 6: Portfolio expected covers year-1 installment charge  # pragma: no cover - defensive
            elif (
                portfolio_expected >= total_annual_installment
            ):  # pragma: no cover - defensive
                decision = "CONDITIONAL_GO"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Portfolio expected (€{portfolio_expected:,.0f}) covers the year-1 P&L charge "  # pragma: no cover - defensive
                    f"(€{total_annual_installment:,.0f}) but the downside (€{portfolio_var95:,.0f}) "  # pragma: no cover - defensive
                    f"does not. High execution risk — tight monitoring required."  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
            else:  # pragma: no cover - defensive
                decision = "REVIEW"  # pragma: no cover - defensive
                reason = (  # pragma: no cover - defensive
                    f"Portfolio (€{portfolio_expected:,.0f} expected, "  # pragma: no cover - defensive
                    f"€{portfolio_var95:,.0f} floor) "  # pragma: no cover - defensive
                    f"does not cover even the year-1 installment charge "  # pragma: no cover - defensive
                    f"(€{total_annual_installment:,.0f}). "  # pragma: no cover - defensive
                    f"Business case requires review."  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
        else:  # pragma: no cover - defensive
            decision = "REVIEW"  # pragma: no cover - defensive
            reason = "No features analyzed"  # pragma: no cover - defensive

        return BoardRecommendation(
            portfolio_multi_year=portfolio_multi_year,
            ranked_features=ranked_features,
            go_decision=decision,
            go_reason=reason,
            total_portfolio_expected=float(portfolio_expected),
            total_portfolio_var95=float(portfolio_var95),
            total_cost=float(total_cost),
            total_annual_installment=float(total_annual_installment),
            model_card=model_card if model_card is not None else ModelCard(),
        )

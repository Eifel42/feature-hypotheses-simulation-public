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

"""Multi-year portfolio P&L simulation domain service."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from fhs.core.model import Feature, RiskLayerStats, ScenarioRiskModel
from fhs.core.model.value_objects.multi_year_pnl import (
    MultiYearLayer,
    MultiYearLayerYear,
    MultiYearPnLMeta,
    MultiYearPnLResult,
    MultiYearRiskProbabilities,
)
from fhs.core.model.value_objects.multi_year_result import MultiYearResult, YearResult
from fhs.core.services.financial import FinancialCalculator
from fhs.core.services.simulation.simulator import FeatureSimulator


class PnLMultiYearService:
    """Build multi-year layered P&L views for selected portfolios."""

    @staticmethod
    def _clamp_probability(value: float, upper: float = 0.95) -> float:
        return float(max(0.0, min(upper, value)))

    @staticmethod
    def _risk_stats(values: np.ndarray) -> RiskLayerStats:
        return RiskLayerStats.from_scenarios(values)

    @classmethod
    def _year_result_from_scenarios(
        cls, year: int, scenarios: np.ndarray
    ) -> YearResult:
        return YearResult.from_scenarios(year=year, scenarios=scenarios)

    @classmethod
    def _multi_year_result_from_arrays(
        cls,
        feature_name: str,
        yearly_arrays: list[np.ndarray],
        *,
        discount_rate: float,
    ) -> MultiYearResult:
        return MultiYearResult(
            feature_name=feature_name,
            years=[
                cls._year_result_from_scenarios(idx + 1, scenarios)
                for idx, scenarios in enumerate(yearly_arrays)
            ],
            discount_rate=discount_rate,
        )

    def simulate(
        self,
        feature_names: Iterable[str],
        *,
        feature_by_name: dict[str, Feature],
        risk_model: ScenarioRiskModel,
        years: int,
        scenarios: int,
        discount_rate: float,
        seed: int,
        service_seed: int,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
    ) -> MultiYearPnLResult:
        """Simulate multi-year layered portfolio P&L and NPV."""
        selected = [name for name in feature_names if name in feature_by_name]
        rate = float(discount_rate)

        empty_layer = MultiYearLayer(
            years=(),
            total_3y=self._risk_stats(np.array([])),
            npv=self._risk_stats(np.array([])),
        )
        if not selected:
            return MultiYearPnLResult(
                investment=0.0,
                discount_rate=rate,
                base=empty_layer,
                risk1=empty_layer,
                risk2=empty_layer,
                component=empty_layer,
                risk3=empty_layer,
                meta=MultiYearPnLMeta(
                    selected=(),
                    years=years,
                    probabilities=MultiYearRiskProbabilities(
                        risk_2=0.0,
                        risk_3=0.0,
                        component_portfolio=0.0,
                    ),
                    delivery_hit_pct={},
                    market_hit_pct_by_year=(),
                    global_hit_pct_by_year=(),
                    cluster_hit_pct_by_year=(),
                ),
            )

        investment = float(
            sum(feature_by_name[name].development_cost for name in selected)
        )
        # Installment schedule: for each year, sum annual_installment of features
        # whose installment period covers that year.
        installment_schedule = tuple(
            float(
                sum(
                    feature_by_name[name].annual_installment
                    for name in selected
                    if yr <= feature_by_name[name].installment_years
                )
            )
            for yr in range(1, years + 1)
        )
        simulated = {
            name: FeatureSimulator(seed=service_seed + idx).simulate_feature_multi_year(
                feature_by_name[name],
                years=years,
                scenarios=scenarios,
                discount_rate=rate,
            )
            for idx, name in enumerate(selected)
        }

        n_scenarios = len(next(iter(simulated.values())).years[0].scenarios)
        rng = np.random.default_rng(seed)

        p2 = self._clamp_probability(
            risk_model.risk_2_market_probability
            if risk2_probability is None
            else risk2_probability
        )
        p3 = self._clamp_probability(
            risk_model.risk_3_global_probability
            if risk3_probability is None
            else risk3_probability
        )

        delivery_gates: dict[str, np.ndarray] = {}
        for idx, name in enumerate(selected):
            feature = feature_by_name[name]
            feature_rng = np.random.default_rng(seed + idx + 3000)
            delivery_gates[name] = feature_rng.random(
                n_scenarios
            ) >= self._clamp_probability(feature.likelihood_of_non_delivery)

        cluster_probabilities: dict[str, float] = {}
        for name in selected:
            cluster = feature_by_name[name].dependency_cluster or "Independent"
            if (
                cluster not in cluster_probabilities
            ):  # pragma: no cover - partial branch
                cluster_probabilities[cluster] = self._clamp_probability(
                    float(
                        risk_model.component_risk_by_cluster.get(
                            cluster,
                            risk_model.default_component_probability,
                        )
                    )
                )

        market_hits_by_year = [rng.random(n_scenarios) < p2 for _ in range(years)]
        global_hits_by_year = [rng.random(n_scenarios) < p3 for _ in range(years)]
        cluster_hits_by_year = [
            {
                cluster: rng.random(n_scenarios) < probability
                for cluster, probability in cluster_probabilities.items()
            }
            for _ in range(years)
        ]

        layer_yearly_arrays: dict[str, list[np.ndarray]] = {
            "base": [],
            "risk1": [],
            "risk2": [],
            "component": [],
            "risk3": [],
        }

        for year_idx in range(years):
            base_total = np.zeros(n_scenarios, dtype=float)
            risk1_total = np.zeros(n_scenarios, dtype=float)
            risk2_total = np.zeros(n_scenarios, dtype=float)
            component_total = np.zeros(n_scenarios, dtype=float)
            risk3_total = np.zeros(n_scenarios, dtype=float)

            market_hits = market_hits_by_year[year_idx]
            global_hits = global_hits_by_year[year_idx]
            cluster_hits = cluster_hits_by_year[year_idx]

            for name in selected:
                feature = feature_by_name[name]
                base_values = simulated[name].years[year_idx].scenarios
                base_total += base_values

                delivered = delivery_gates[name]
                after_r1 = base_values * delivered
                risk1_total += after_r1

                after_r2 = after_r1 * np.where(
                    market_hits,
                    risk_model.risk_2_market_multiplier,
                    1.0,
                )
                risk2_total += after_r2

                cluster = feature.dependency_cluster or "Independent"
                after_component = after_r2 * np.where(
                    cluster_hits[cluster],
                    risk_model.component_risk_multiplier,
                    1.0,
                )
                component_total += after_component

                after_r3 = after_component * np.where(
                    global_hits,
                    risk_model.risk_3_global_multiplier,
                    1.0,
                )
                risk3_total += after_r3

            layer_yearly_arrays["base"].append(base_total)
            layer_yearly_arrays["risk1"].append(risk1_total)
            layer_yearly_arrays["risk2"].append(risk2_total)
            layer_yearly_arrays["component"].append(component_total)
            layer_yearly_arrays["risk3"].append(risk3_total)

        multi_year_layers = {
            layer: self._multi_year_result_from_arrays(
                f"Selected Portfolio ({layer})",
                arrays,
                discount_rate=rate,
            )
            for layer, arrays in layer_yearly_arrays.items()
        }

        summarized_layers: dict[str, MultiYearLayer] = {}
        for layer_name, result in multi_year_layers.items():
            total_3y_scenarios = FinancialCalculator.cumulative_scenarios(
                [year.scenarios for year in result.years]
            )
            npv_scenarios = (
                FinancialCalculator.result_npv_scenarios(result) - investment
            )
            summarized_layers[layer_name] = MultiYearLayer(
                years=tuple(
                    MultiYearLayerYear(
                        year=year.year,
                        expected=year.expected,
                        var_95=year.var_95,
                        cvar_95=year.cvar_95,
                        std=year.std,
                    )
                    for year in result.years
                ),
                total_3y=self._risk_stats(total_3y_scenarios),
                npv=self._risk_stats(npv_scenarios),
            )

        portfolio_component_probability = 1.0
        for probability in cluster_probabilities.values():
            portfolio_component_probability *= 1.0 - probability

        return MultiYearPnLResult(
            investment=investment,
            discount_rate=rate,
            base=summarized_layers["base"],
            risk1=summarized_layers["risk1"],
            risk2=summarized_layers["risk2"],
            component=summarized_layers["component"],
            risk3=summarized_layers["risk3"],
            meta=MultiYearPnLMeta(
                selected=tuple(selected),
                years=years,
                probabilities=MultiYearRiskProbabilities(
                    risk_2=p2,
                    risk_3=p3,
                    component_portfolio=1.0 - portfolio_component_probability,
                ),
                delivery_hit_pct={
                    name: float(np.mean(~delivery_gates[name])) for name in selected
                },
                market_hit_pct_by_year=tuple(
                    float(np.mean(hits)) for hits in market_hits_by_year
                ),
                global_hit_pct_by_year=tuple(
                    float(np.mean(hits)) for hits in global_hits_by_year
                ),
                cluster_hit_pct_by_year=tuple(
                    {
                        cluster: float(np.mean(hits))
                        for cluster, hits in hits_by_cluster.items()
                    }
                    for hits_by_cluster in cluster_hits_by_year
                ),
            ),
            installment_schedule=installment_schedule,
        )

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

"""Multi-year simulations, NPV/IRR, and long-term portfolio metrics operations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fhs.application.portfolio_context import PortfolioContext
from fhs.core.model import (
    FinancialViewResult,
    MultiYearPnLResult,
    MultiYearResult,
    ScenarioRiskModel,
)
from fhs.core.services import FinancialCalculator
from fhs.core.services.risk import PortfolioLayerRiskService
from fhs.core.services.simulation import PnLMultiYearService, PortfolioMultiYearService


class MultiYearAnalysisOperations:
    """Multi-year simulations, NPV/IRR, and long-term portfolio metrics with explicit context."""

    def __init__(self, context: PortfolioContext):
        self._context = context
        self._pnl_multi_year_service = PnLMultiYearService()
        self._portfolio_multi_year_service = PortfolioMultiYearService()

    # noinspection PyTypeHintsInspection
    def simulate_pnl(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        years: int = 3,
        discount_rate: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        seed: int = 42,
    ) -> MultiYearPnLResult:
        """Simulate 3-year portfolio risk with path-wise P&L and NPV.

        Model choice:
        - Delivery risk is a one-time launch gate per feature across the full horizon.
        - Market, component, and global risks are simulated annually.
        - Upfront investment is subtracted once at the NPV layer.

        This is a better fit for roadmap economics than repeating non-delivery
        every year, because a feature either ships or it does not.
        """
        rate = self._context.discount_rate if discount_rate is None else discount_rate
        feature_by_name = {f.name: f for f in self._context.features}
        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        return self._pnl_multi_year_service.simulate(  # type: ignore[return-value]
            feature_names,
            feature_by_name=feature_by_name,
            risk_model=normalized,
            years=years,
            scenarios=self._context.scenarios,
            discount_rate=rate,
            seed=seed,
            service_seed=self._context.seed,
            risk2_probability=risk2_probability,
            risk3_probability=risk3_probability,
        )

    def simulate_portfolio(
        self,
        names: Iterable[str],
        *,
        years: int = 3,
        discount_rate: float | None = None,
    ) -> MultiYearResult:
        """Combined multi-year simulation for selected features."""
        feature_by_name = {f.name: f for f in self._context.features}
        return self._portfolio_multi_year_service.simulate(  # type: ignore[return-value]
            selected=self._context.resolve_names(names),
            feature_by_name=feature_by_name,
            years=years,
            scenarios=self._context.scenarios,
            discount_rate=(
                self._context.discount_rate if discount_rate is None else discount_rate
            ),
            seed=self._context.seed,
        )

    def financial_view(
        self,
        names: Iterable[str],
        *,
        investment: float,
        discount_rate: float | None = None,
    ) -> FinancialViewResult:
        """NPV/IRR summary for selected portfolio."""
        rate = self._context.discount_rate if discount_rate is None else discount_rate
        multi_year = self.simulate_portfolio(
            names,
            years=3,
            discount_rate=rate,
        )
        return FinancialCalculator.result_financial_view(
            multi_year,
            investment=investment,
            discount_rate=rate,
        )

    # noinspection PyTypeHintsInspection
    def component_risk_summary(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        years: int = 3,
        discount_rate: float | None = None,
    ):
        """Named component risk metrics across a multi-year horizon."""
        from fhs.core.services.risk import PortfolioRiskAttributionService

        selected = self._context.resolve_names(feature_names)
        feature_by_name = {f.name: f for f in self._context.features}
        rate = self._context.discount_rate if discount_rate is None else discount_rate
        normalized_risk_model = PortfolioLayerRiskService.normalize_risk_model(
            risk_model
        )

        def cluster_business_value(feat_names: tuple[str, ...]) -> tuple[float, float]:
            cluster_result = self.simulate_portfolio(
                feat_names,
                years=years,
                discount_rate=rate,
            )
            expected_business_value_3y = FinancialCalculator.result_total_3y_expected(
                cluster_result
            )
            expected_npv_business_value = FinancialCalculator.result_npv_expected(
                cluster_result
            )
            return float(expected_business_value_3y), float(expected_npv_business_value)

        def _clamp_probability(value: float, upper: float = 0.95) -> float:
            return PortfolioLayerRiskService.clamp_probability(value, upper=upper)

        return (
            PortfolioRiskAttributionService.portfolio_component_risk_summary_multi_year(
                selected=selected,
                feature_by_name=feature_by_name,
                normalized_risk_model=normalized_risk_model,
                cluster_business_value_function=cluster_business_value,
                clamp_probability=_clamp_probability,
            )
        )

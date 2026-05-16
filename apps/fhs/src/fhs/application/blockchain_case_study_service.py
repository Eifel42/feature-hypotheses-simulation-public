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

"""Application service for the blockchain case-study notebooks.

This service keeps notebook cells short and reuses the DDD model:
- scenario data comes from ``load_scenario()``
- simulations come from ``FeatureSimulator``
- financial KPIs come from ``FinancialCalculator``
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from fhs.core.model import Feature, RiskLayerStats
from fhs.core.model.value_objects import (
    FeatureYear1Result,
    MultiYearResult,
    OperatingCostResult,
    PLVariantRow,
    PortfolioPLVariants,
    PortfolioSnapshot,
    YearResult,
)
from fhs.core.services import FeatureSimulator, FinancialCalculator

from .calculation_service import FeatureCalculationService

if TYPE_CHECKING:
    from fhs.core.model.value_objects.financial_view import IrrSummary, NpvSummary

PORTFOLIO_TOTAL_NAME = "Portfolio Total"


class BlockchainCaseStudyService:
    """Reusable calculations for notebook 02 and 03."""

    def __init__(self, *, seed: int = 42, scenarios: int = 100_000):
        self.seed = seed
        self.scenarios = scenarios
        self._simulator = FeatureSimulator(seed=seed)

    @staticmethod
    def _sorted_keys(mapping: Mapping[str, Any]) -> list[str]:
        return sorted(mapping.keys())

    @staticmethod
    def _short_name(feature: Feature) -> str:
        return feature.name.split(": ", 1)[-1]

    @staticmethod
    def expected_business_value(feature: Feature) -> float:
        """Deterministic expected business value helper for notebook table rendering."""
        return FeatureCalculationService.calculate_expected_business_value(
            feature
        )  # pragma: no cover - defensive

    @staticmethod
    def roi(feature: Feature) -> float:
        """Deterministic ROI helper for notebook table rendering."""
        return FeatureCalculationService.calculate_roi(
            feature
        )  # pragma: no cover - defensive

    def simulate_year1(
        self,
        features_by_key: Mapping[str, Feature],
    ) -> dict[str, FeatureYear1Result]:
        """Simulate one-year business value distributions per feature (in EUR)."""
        results: dict[str, FeatureYear1Result] = {}

        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            simulation = self._simulator.simulate_feature(
                feature,
                scenarios=self.scenarios,
            )
            scenarios_eur = (
                simulation.results_array * feature.business_value_per_conversion
            )

            results[key] = FeatureYear1Result(
                key=key,
                feature=feature,
                result=simulation,
                scenarios_eur=scenarios_eur,
                expected_eur=float(simulation.expected_business_value),
                var_95_eur=float(simulation.business_value_at_risk_95),
                cvar_95_eur=float(
                    simulation.cvar_95 * feature.business_value_per_conversion
                ),
                p95_eur=float(simulation.p95 * feature.business_value_per_conversion),
                std_eur=float(simulation.std * feature.business_value_per_conversion),
                roi=FeatureCalculationService.calculate_roi(feature),
            )

        return results

    def chart_payload(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
    ) -> dict[str, dict[str, Any]]:
        """Create chart input format used by notebook chart helpers."""
        payload: dict[str, dict[str, Any]] = {}  # pragma: no cover - defensive
        # pragma: no cover - defensive
        for key in self._sorted_keys(year1_results):  # pragma: no cover - defensive
            row = year1_results[key]  # pragma: no cover - defensive
            payload[key] = {  # pragma: no cover - defensive
                "scenarios": row.scenarios_eur,  # pragma: no cover - defensive
                "expected": row.expected_eur,  # pragma: no cover - defensive
                "var95": row.var_95_eur,  # pragma: no cover - defensive
                "p95": row.p95_eur,  # pragma: no cover - defensive
                "name": self._short_name(row.feature),  # pragma: no cover - defensive
            }  # pragma: no cover - defensive
        # pragma: no cover - defensive
        return payload  # pragma: no cover - defensive

    def portfolio_year1(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
    ) -> PortfolioSnapshot:
        """Combine all year-1 feature scenarios into one portfolio view."""
        keys = self._sorted_keys(year1_results)
        if not keys:
            return PortfolioSnapshot(  # pragma: no cover - defensive
                expected=0.0,
                var_95=0.0,
                cvar_95=0.0,
                std_dev=0.0,
                investment=0.0,
            )

        combined = np.sum(
            [year1_results[key].scenarios_eur for key in keys],
            axis=0,
        )
        stats = RiskLayerStats.from_scenarios(combined)
        return PortfolioSnapshot(
            expected=stats.expected,
            var_95=stats.var_95,
            cvar_95=stats.cvar_95,
            std_dev=stats.std,
            investment=float(
                sum(year1_results[key].feature.development_cost for key in keys)
            ),
        )

    def simulate_multi_year(
        self,
        features_by_key: Mapping[str, Feature],
        *,
        discount_rate: float,
        years: int = 3,
    ) -> dict[str, MultiYearResult]:
        """Simulate multi-year business value distributions per feature.

        Values are already in EUR. No additional scaling is needed.
        """
        results: dict[str, MultiYearResult] = {}

        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            results[key] = self._simulator.simulate_feature_multi_year(
                feature=feature,
                years=years,
                scenarios=self.scenarios,
                discount_rate=discount_rate,
            )

        return results

    def combine_multi_year_results(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        *,
        discount_rate: float,
        name: str = PORTFOLIO_TOTAL_NAME,
    ) -> MultiYearResult:
        """Aggregate feature multi-year results into a portfolio result."""
        keys = self._sorted_keys(multi_year_results)
        if not keys:
            return MultiYearResult(  # pragma: no cover - defensive
                feature_name=name,
                years=[],
                discount_rate=discount_rate,
            )

        n_years = len(multi_year_results[keys[0]].years)
        years: list[YearResult] = []

        for idx in range(n_years):
            year_scenarios = np.sum(
                [multi_year_results[key].years[idx].scenarios for key in keys],
                axis=0,
            )
            years.append(
                YearResult.from_scenarios(year=idx + 1, scenarios=year_scenarios)
            )

        return MultiYearResult(
            feature_name=name,
            years=years,
            discount_rate=discount_rate,
        )

    @staticmethod
    def total_investment(features_by_key: Mapping[str, Feature]) -> float:
        """Sum development costs for all features."""
        return float(sum(f.development_cost for f in features_by_key.values()))

    @staticmethod
    def total_annual_opex(features_by_key: Mapping[str, Feature]) -> float:
        """Sum annual operating costs for all features."""
        return float(sum(f.annual_operating_cost for f in features_by_key.values()))

    @staticmethod
    def net_multi_year_scenarios(
        result: MultiYearResult,
        annual_opex: float,
    ) -> MultiYearResult:
        """Return a copy of result with annual OpEx deducted from every year's scenarios.

        Used to convert gross business-value scenarios into net cash-flow scenarios
        before computing NPV and IRR, so that operating costs are reflected in the
        capital-budgeting metrics.

        Args:
            result: Multi-year simulation result with gross business-value scenarios.
            annual_opex: Operating cost per year in EUR (same amount deducted each year).

        Returns:
            New MultiYearResult with ``scenarios = gross_bv − annual_opex`` per year.
        """
        net_years = [
            YearResult.from_scenarios(
                year=yr.year,
                scenarios=yr.scenarios - annual_opex,
            )
            for yr in result.years
        ]
        return MultiYearResult(
            feature_name=result.feature_name,
            years=net_years,
            discount_rate=result.discount_rate,
        )

    def roi_rows(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
    ) -> list[tuple[str, ...]]:
        """Formatted rows for ROI comparison table.

        Columns: Feature, Investment, Annual OpEx, Expected BV,
                 ROI (gross), Net ROI (after OpEx).

        Net ROI formula:

            (R1 - C_dev - C_opex) / C_dev
        """
        rows: list[tuple[str, ...]] = []

        for key in self._sorted_keys(year1_results):
            row = year1_results[key]
            f = row.feature
            opex = f.annual_operating_cost
            net_roi = (
                (row.expected_eur - f.development_cost - opex) / f.development_cost
                if f.development_cost
                else 0.0
            )
            rows.append(
                (
                    f.name,
                    f"€{f.development_cost:,.0f}",
                    f"€{opex:,.0f}",
                    f"€{row.expected_eur:,.0f}",
                    f"{row.roi:.1%}",
                    f"{net_roi:.1%}",
                )
            )

        return rows

    def sample_conversion_rates(
        self,
        feature: Feature,
        *,
        scenarios: int = 1_000,
    ) -> np.ndarray:
        """Sample conversion rates for notebook walkthroughs.

        Uses the internal simulator and returns per-scenario conversion rates
        in the [0, 1] range so notebooks can explain uncertainty without
        importing low-level simulation engines directly.
        """
        simulation = self._simulator.simulate_feature(
            feature, scenarios=scenarios
        )  # pragma: no cover - defensive
        if feature.expected_users <= 0:  # pragma: no cover - defensive
            return np.zeros(scenarios, dtype=float)  # pragma: no cover - defensive
        rates = simulation.results_array / float(
            feature.expected_users
        )  # pragma: no cover - defensive
        return np.asarray(
            np.clip(rates, 0.0, 1.0), dtype=float
        )  # pragma: no cover - defensive

    def npv_rows(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        features_by_key: Mapping[str, Feature],
        *,
        discount_rate: float,
    ) -> list[tuple[str, ...]]:
        """Formatted rows for NPV table (net of annual OpEx).

        Cash flows per year = gross business value − annual_operating_cost.
        NPV formula (V1 cash-flow view):

            NPV = -C_dev + sum_t( (R_t - C_opex) / (1+r)^t )
        """
        rows: list[tuple[str, ...]] = []

        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            net_result = self.net_multi_year_scenarios(
                multi_year_results[key],
                feature.annual_operating_cost,
            )
            npv = FinancialCalculator.result_npv(
                net_result,
                feature.development_cost,
                discount_rate,
            )
            rows.append(
                (
                    feature.name,
                    f"€{feature.development_cost:,.0f}",
                    f"€{npv.expected:,.0f}",
                    f"€{npv.var_95:,.0f}",
                    f"€{npv.p95:,.0f}",
                )
            )

        return rows

    def irr_rows(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        features_by_key: Mapping[str, Feature],
    ) -> list[tuple[str, ...]]:
        """Formatted rows for IRR table (net of annual OpEx).

        Cash flows per year = gross business value − annual_operating_cost.
        IRR is the rate r* that satisfies:

            0 = -C_dev + sum_t( (R_t - C_opex) / (1+r*)^t )
        """
        rows: list[tuple[str, ...]] = []

        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            net_result = self.net_multi_year_scenarios(
                multi_year_results[key],
                feature.annual_operating_cost,
            )
            irr = FinancialCalculator.result_irr(
                net_result,
                feature.development_cost,
            )
            rows.append(
                (
                    feature.name,
                    f"€{feature.development_cost:,.0f}",
                    f"{irr.expected:.0%}",
                    f"{irr.floor:.0%}",
                    f"{irr.ceiling:.0%}",
                )
            )

        return rows

    @staticmethod
    def portfolio_total_3y_expected(portfolio_result: MultiYearResult) -> float:
        """Expected cumulative 3-year business value for a portfolio result."""
        return FinancialCalculator.result_total_3y_expected(
            portfolio_result
        )  # pragma: no cover - defensive

    def npv_dual_rows(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        features_by_key: Mapping[str, Feature],
        *,
        discount_rate: float,
    ) -> list[tuple]:
        """NPV rows with Option A (upfront) and Option B (installment) columns.

        Each row:
            (name, dev_cost, installment, installment_years,
             npv_a_exp, npv_a_floor, npv_a_ceil,
             npv_b_exp, npv_b_floor, npv_b_ceil,
             npv_diff_exp)

        Option A: NPV = −C_dev + Σ (R_t − OpEx)/(1+r)^t
        Option B: NPV = −Inst  + Σ (R_t − Inst − OpEx)/(1+r)^t  (years 1..n-1)
                               + Σ (R_t − OpEx)/(1+r)^t          (years n..T)
        """
        rows: list[tuple] = []
        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            net_result = self.net_multi_year_scenarios(
                multi_year_results[key],
                feature.annual_operating_cost,
            )
            npv_a = FinancialCalculator.result_npv(
                net_result, feature.development_cost, discount_rate
            )
            npv_b = FinancialCalculator.result_npv_installment(
                net_result,
                feature.annual_installment,
                feature.installment_years,
                discount_rate,
            )
            rows.append(
                (
                    self._short_name(feature),
                    feature.development_cost,
                    feature.annual_installment,
                    feature.installment_years,
                    npv_a.expected,
                    npv_a.var_95,
                    npv_a.p95,
                    npv_b.expected,
                    npv_b.var_95,
                    npv_b.p95,
                    npv_b.expected - npv_a.expected,  # diff: B − A
                )
            )
        return rows

    def irr_dual_rows(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        features_by_key: Mapping[str, Feature],
    ) -> list[tuple]:
        """IRR rows with Option A (upfront) and Option B (installment) columns.

        Each row:
            (name, dev_cost, installment, installment_years,
             irr_a_exp, irr_a_floor, irr_a_ceil,
             irr_b_exp, irr_b_floor, irr_b_ceil)

        IRR B may be NaN when all net cashflows are positive (no sign change).
        """
        rows: list[tuple] = []
        for key in self._sorted_keys(features_by_key):
            feature = features_by_key[key]
            net_result = self.net_multi_year_scenarios(
                multi_year_results[key],
                feature.annual_operating_cost,
            )
            irr_a = FinancialCalculator.result_irr(net_result, feature.development_cost)
            irr_b = FinancialCalculator.irr_installment_from_scenarios(
                feature.annual_installment,
                feature.installment_years,
                [y.scenarios for y in net_result.years],
            )
            rows.append(
                (
                    self._short_name(feature),
                    feature.development_cost,
                    feature.annual_installment,
                    feature.installment_years,
                    irr_a.expected,
                    irr_a.floor,
                    irr_a.ceiling,
                    irr_b.expected,
                    irr_b.floor,
                    irr_b.ceiling,
                )
            )
        return rows

    def portfolio_npv_installment(
        self,
        portfolio_myr: MultiYearResult,
        features_by_key: Mapping[str, Feature],
        total_annual_opex: float,
        discount_rate: float,
        years: int = 3,
    ) -> NpvSummary:
        """Portfolio NPV under installment financing (Option B).

        First installment at Year 0; remaining installments in years 1..(n-1).
        Features with shorter ``installment_years`` stop contributing once
        their window expires.

        Year 0: all features pay their first installment.
        Year t ∈ [1, max_n-1]: features where t < installment_years.
        """
        schedule = self.installment_schedule(features_by_key, years=years)
        year0 = schedule[0]
        per_year = schedule[1:]
        net_result = self.net_multi_year_scenarios(portfolio_myr, total_annual_opex)
        return FinancialCalculator.result_npv_installment_schedule(
            net_result,
            per_year,
            discount_rate,
            year0_installment=year0,
        )

    def portfolio_irr_installment(
        self,
        portfolio_myr: MultiYearResult,
        features_by_key: Mapping[str, Feature],
        total_annual_opex: float,
        years: int = 3,
    ) -> IrrSummary:
        """Portfolio IRR under installment financing (Option B).

        First installment at Year 0; remaining installments in years 1..(n-1).
        Features with shorter ``installment_years`` are not over-charged.
        """
        schedule = self.installment_schedule(features_by_key, years=years)
        year0 = schedule[0]
        per_year = schedule[1:]
        net_result = self.net_multi_year_scenarios(portfolio_myr, total_annual_opex)
        return FinancialCalculator.irr_installment_from_scenarios_schedule(
            per_year,
            [y.scenarios for y in net_result.years],
            year0_installment=year0,
        )

    @staticmethod
    def installment_schedule(
        features_by_key: Mapping[str, Feature],
        years: int = 3,
    ) -> list[float]:
        """Return portfolio installment totals for Year 0..Year n-1.

        The first element is the Year-0 installment load. Subsequent elements
        represent remaining installment totals for each following year.
        """
        return [
            float(
                sum(
                    f.annual_installment
                    for f in features_by_key.values()
                    if year == 0 or year < f.installment_years
                )
            )
            for year in range(years)
        ]

    # noinspection PyUnusedLocal
    @staticmethod
    def financing_recommendation(
        npv_a: NpvSummary,
        npv_b: NpvSummary,
        irr_a: IrrSummary,
        irr_b: IrrSummary,
        total_investment: float,
        total_annual_installment: float,
        installment_years: int,
        discount_rate: float,
        installment_schedule: Sequence[float] | None = None,
    ) -> str:
        """Plain-English financing recommendation comparing Option A vs Option B.

        Args:
            npv_a: NPV under upfront financing.
            npv_b: NPV under installment financing.
            irr_a: IRR under upfront financing.
            irr_b: IRR under installment financing.
            total_investment: Full portfolio investment cost.
            total_annual_installment: Year-0 installment total across all features.
            installment_years: Longest installment period in the portfolio.
            discount_rate: Discount rate used for NPV.
            installment_schedule: Optional Year-0..Year n-1 installment totals.

        Returns:
            Multi-sentence recommendation string.
        """
        import math

        parts: list[str] = []
        default_schedule = [total_annual_installment] * max(installment_years, 1)
        nonzero_schedule = [
            float(amount)
            for amount in (
                installment_schedule
                if installment_schedule is not None
                else default_schedule
            )
            if float(amount) > 0
        ]
        unique_levels = {round(amount, 2) for amount in nonzero_schedule}
        if len(nonzero_schedule) == 1:
            schedule_phrase = f"a single installment of €{nonzero_schedule[0]:,.0f}"  # pragma: no cover - defensive
        elif len(unique_levels) == 1:
            schedule_phrase = f"{len(nonzero_schedule)} annual payments of €{nonzero_schedule[0]:,.0f}"
        else:
            schedule_items = ", ".join(
                f"Year {year}: €{amount:,.0f}"
                for year, amount in enumerate(nonzero_schedule)
            )
            schedule_phrase = f"a declining installment schedule ({schedule_items})"

        # NPV comparison
        npv_diff = npv_b.expected - npv_a.expected
        if npv_diff > 0:
            parts.append(
                f"Option B (installment) produces a higher expected NPV "
                f"(+€{npv_diff:,.0f} vs Option A). "
                f"Spreading the €{total_investment:,.0f} investment into "
                f"{schedule_phrase} "
                f"captures the time value of money at a {discount_rate:.0%} discount rate — "
                "later payments are worth less in today's terms."
            )
        else:
            parts.append(  # pragma: no cover - defensive
                f"Option A (upfront) and Option B (installment) produce similar NPVs "
                f"(difference: €{abs(npv_diff):,.0f}). "
                f"The installment schedule does not materially improve the present value."
            )

        # IRR comparison
        irr_a_val = float(irr_a.expected)
        irr_b_val = float(irr_b.expected)
        if math.isnan(irr_b_val):
            parts.append(
                "Option B IRR is undefined — the portfolio generates positive net cash flows "
                "in every installment year, so there is no rate that makes NPV equal zero. "
                "This is a favourable sign: the investment pays back from year 1."
            )
        elif irr_b_val > irr_a_val:  # pragma: no cover - partial branch
            parts.append(
                f"IRR (Option B: {irr_b_val:.0%}) exceeds IRR (Option A: {irr_a_val:.0%}). "
                f"Each euro of annual outlay generates a higher return under installment financing."
            )

        # Floor risk
        if npv_a.var_95 < 0 <= npv_b.var_95:
            parts.append(
                "Importantly, the downside floor (BVF 95%) is negative under Option A "
                "but remains positive under Option B — installment financing substantially "
                "reduces year-1 cash-at-risk."
            )
        elif npv_b.var_95 < 0:
            parts.append(  # pragma: no cover - defensive
                f"Both options carry downside floor risk (BVF 95% < 0). "
                f"Option B floor: €{npv_b.var_95:,.0f}; "
                f"confirm multi-year recovery before committing."
            )

        # Simple budget note
        if (
            total_annual_installment < total_investment * 0.6
        ):  # pragma: no cover - partial branch
            if len(unique_levels) == 1:
                parts.append(
                    f"Budget note: Option B requires only €{total_annual_installment:,.0f}/yr "
                    f"vs €{total_investment:,.0f} upfront — freeing budget for other initiatives."
                )
            else:
                last_amount = nonzero_schedule[-1]
                last_year = len(nonzero_schedule) - 1
                parts.append(
                    f"Budget note: Option B starts at €{total_annual_installment:,.0f} in Year 0 "
                    f"vs €{total_investment:,.0f} upfront, then falls to €{last_amount:,.0f} "
                    f"by Year {last_year} as shorter amortizations roll off."
                )

        return " ".join(parts)

    def feature_cashflow_schedules(
        self,
        multi_year_results: Mapping[str, MultiYearResult],
        features_by_key: Mapping[str, Feature],
        discount_rate: float,
    ) -> tuple[dict, dict]:
        """Per-feature cashflow schedules (rows) × years (columns) for Option A and B.

        Each schedule dict contains:
            label:            display name for the table header
            inv_label:        short description of the investment structure
            years:            [0, 1, 2, ..., n]
            discount_factors: [1/(1+r)^t for t in years]
            rows:             list of {name, cashflows, npv} — one per feature
            portfolio:        {name, cashflows, npv} — sum of all features

        Net cash flow per year:
            Option A — Year 0: −dev_cost, Years 1..T: BV_expected − OpEx
            Option B — Year 0: 0, Years 1..n: BV − Inst − OpEx, Years n+1..T: BV − OpEx

        Args:
            multi_year_results: Per-feature multi-year simulation results.
            features_by_key:    Feature definitions.
            discount_rate:      Discount rate for NPV computation.

        Returns:
            Tuple (sched_a, sched_b).
        """
        keys = self._sorted_keys(features_by_key)
        n_years = max(len(multi_year_results[k].years) for k in keys)
        dfs = [1.0 / (1 + discount_rate) ** t for t in range(n_years + 1)]
        years = list(range(n_years + 1))

        rows_a: list[dict] = []
        rows_b: list[dict] = []
        portfolio_cfs_a = [0.0] * (n_years + 1)
        portfolio_cfs_b = [0.0] * (n_years + 1)

        for key in keys:
            feature = features_by_key[key]
            myr = multi_year_results[key]
            short_name = self._short_name(feature)
            bv_per_year = [yr.expected for yr in myr.years]

            # Option A — full investment at Year 0
            # round() applied to every cashflow so all displayed values are whole euros
            cfs_a: list[float] = [round(-feature.development_cost)]
            for bv in bv_per_year:
                cfs_a.append(round(bv - feature.annual_operating_cost))
            npv_a = round(sum(cf * df for cf, df in zip(cfs_a, dfs, strict=False)))
            rows_a.append({"name": short_name, "cashflows": cfs_a, "npv": npv_a})

            # Option B — first installment at Year 0; remaining in years 1..(n-1)
            cfs_b: list[float] = [round(-feature.annual_installment)]
            for t, bv in enumerate(bv_per_year):
                year_num = t + 1
                inst = (
                    feature.annual_installment
                    if year_num < feature.installment_years
                    else 0.0
                )
                cfs_b.append(round(bv - inst - feature.annual_operating_cost))
            npv_b = round(sum(cf * df for cf, df in zip(cfs_b, dfs, strict=False)))
            rows_b.append({"name": short_name, "cashflows": cfs_b, "npv": npv_b})

            for t in range(n_years + 1):
                portfolio_cfs_a[t] += cfs_a[t]
                portfolio_cfs_b[t] += cfs_b[t]

        # Portfolio cashflows are sums of rounded per-feature values — already whole euros.
        # Portfolio NPV is rounded independently; may differ from sum of feature NPVs by ±1
        # (expected rounding behaviour when summing individually rounded components).
        portfolio_npv_a = round(
            sum(cf * df for cf, df in zip(portfolio_cfs_a, dfs, strict=False))
        )
        portfolio_npv_b = round(
            sum(cf * df for cf, df in zip(portfolio_cfs_b, dfs, strict=False))
        )

        sched_a: dict = {
            "label": "Option A — Upfront Payment",
            "inv_label": "Full investment charged at Year 0",
            "years": years,
            "discount_factors": dfs,
            "rows": rows_a,
            "portfolio": {
                "name": PORTFOLIO_TOTAL_NAME,
                "cashflows": portfolio_cfs_a,
                "npv": portfolio_npv_a,
            },
        }
        sched_b: dict = {
            "label": "Option B — Installment Financing",
            "inv_label": "Investment spread over annual installments (no Year-0 outlay)",
            "years": years,
            "discount_factors": dfs,
            "rows": rows_b,
            "portfolio": {
                "name": PORTFOLIO_TOTAL_NAME,
                "cashflows": portfolio_cfs_b,
                "npv": portfolio_npv_b,
            },
        }
        return sched_a, sched_b

    @staticmethod
    def portfolio_profitability_index(
        npv_a: NpvSummary,
        npv_b: NpvSummary,
        features_by_key: Mapping[str, Feature],
        total_investment: float,
        discount_rate: float,
        years: int = 3,
    ) -> tuple[float, float]:
        """Profitability Index for Option A and Option B.

        PI = NPV / PV(investment)

        Option A: PV(investment) = total_cost (at t=0, no discounting)
        Option B: PV(investment) = PV of the installment stream, i.e.
                  sum(inst_t / (1+r)^t for t in 1..T)
                  where inst_t is the total portfolio installment due in year t.

        Best practice reference: Brealey, Myers & Allen — Principles of
        Corporate Finance, Capital Rationing chapter.

        Args:
            npv_a:           NPV summary under Option A (upfront).
            npv_b:           NPV summary under Option B (installment).
            features_by_key: Feature definitions — used to compute per-year
                             installment totals.
            total_investment: Sum of all development costs (Option A basis).
            discount_rate:   Discount rate used for NPV.
            years:           Number of projection years.

        Returns:
            Tuple (pi_a, pi_b).
        """
        pi_a = (
            npv_a.expected / total_investment if total_investment > 0 else float("nan")
        )

        # Year 0: all features pay their first installment (df=1.0)
        year0 = float(sum(f.annual_installment for f in features_by_key.values()))
        # Years 1..(n-1): only features still within their window
        pv_inst = year0 + float(
            sum(
                sum(
                    f.annual_installment
                    for f in features_by_key.values()
                    if t < f.installment_years
                )
                / (1 + discount_rate) ** t
                for t in range(1, years + 1)
            )
        )
        pi_b = npv_b.expected / pv_inst if pv_inst > 0 else float("nan")

        return pi_a, pi_b

    @staticmethod
    def portfolio_npv(
        portfolio_result: MultiYearResult,
        investment: float,
        discount_rate: float,
    ):
        """Portfolio NPV summary via application-layer wrapper."""
        return FinancialCalculator.result_npv(
            portfolio_result,
            investment,
            discount_rate,
        )

    @staticmethod
    def assess_portfolio_npv(npv_result):
        """Assess NPV summary via application-layer wrapper."""
        return FinancialCalculator.assess_npv(npv_result)

    @staticmethod
    def portfolio_irr(portfolio_result: MultiYearResult, investment: float):
        """Portfolio IRR summary via application-layer wrapper."""
        return FinancialCalculator.result_irr(portfolio_result, investment)

    @staticmethod
    def assess_portfolio_irr(irr_result, discount_rate: float):
        """Assess IRR summary via application-layer wrapper."""
        return FinancialCalculator.assess_irr(
            irr_result, discount_rate
        )  # pragma: no cover - defensive

    def cost_variant_rows(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
    ) -> list[tuple[str, ...]]:
        """Cost variant table rows for the feature overview section.

        One row per feature:
        - Variant 1 (cash-flow): expected BV − full dev cost − year-1 opex
        - Variant 2 (P&L):       expected BV − annual installment − year-1 opex

        Args:
            year1_results: Year-1 simulation results keyed by feature key.

        Returns:
            List of string tuples ready for ``show.samples()``.
        """
        rows: list[tuple[str, ...]] = []
        for key in self._sorted_keys(year1_results):
            row = year1_results[key]
            f = row.feature
            expected = row.expected_eur
            v1 = FeatureCalculationService.net_value_full_cost_year1(f, expected)
            v2 = FeatureCalculationService.net_value_pl_year1(f, expected)

            def _fmt(v: float) -> str:
                sign = "+" if v >= 0 else "−"
                return f"{sign}€{abs(v):,.0f}"

            rows.append(
                (
                    f.name,
                    f"€{expected:,.0f}",
                    f"€{f.development_cost:,.0f}",
                    f"€{f.annual_operating_cost:,.0f}",
                    _fmt(v1),
                    f"€{f.annual_installment:,.0f}",
                    _fmt(v2),
                )
            )
        return rows

    def year1_overview_rows(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
        portfolio: PortfolioSnapshot,
    ) -> list[tuple]:
        """Year-1 overview table rows: BV stats + costs + net values per feature.

        Each feature row:
            (name, expected, var_95, cvar_95,
             development_cost, annual_operating_cost, v1_net,
             annual_installment, v2_net, is_total)

        Last row is the portfolio total (is_total=True).
        """

        def _net(bv: float, invest: float, opex: float) -> float:
            return bv - invest - opex

        rows: list[tuple] = []
        for key in self._sorted_keys(year1_results):
            row = year1_results[key]
            f = row.feature
            rows.append(
                (
                    f.name.split(": ", 1)[-1],  # short name
                    row.expected_eur,
                    row.var_95_eur,
                    row.cvar_95_eur,
                    f.development_cost,
                    f.annual_operating_cost,
                    _net(row.expected_eur, f.development_cost, f.annual_operating_cost),
                    f.annual_installment,
                    _net(
                        row.expected_eur, f.annual_installment, f.annual_operating_cost
                    ),
                    False,  # is_total
                )
            )

        # Portfolio total row
        keys = self._sorted_keys(year1_results)
        total_invest = sum(year1_results[k].feature.development_cost for k in keys)
        total_opex = sum(year1_results[k].feature.annual_operating_cost for k in keys)
        total_depr = sum(year1_results[k].feature.annual_installment for k in keys)
        rows.append(
            (
                PORTFOLIO_TOTAL_NAME,
                portfolio.expected,
                portfolio.var_95,
                portfolio.cvar_95,
                float(total_invest),
                float(total_opex),
                _net(portfolio.expected, float(total_invest), float(total_opex)),
                float(total_depr),
                _net(portfolio.expected, float(total_depr), float(total_opex)),
                True,  # is_total
            )
        )
        return rows

    def simulate_operating_costs(
        self,
        features_by_key: Mapping[str, Feature],
        cost_inflation_max: float = 0.25,
    ) -> OperatingCostResult:
        """Simulate portfolio operating costs with shared cost inflation.

        One inflation factor is drawn from Uniform(0, cost_inflation_max) per
        scenario and applied to all features — shared infrastructure assumption.

        Args:
            features_by_key: Mapping of feature key → Feature (from scenario).
            cost_inflation_max: Maximum inflation rate. Default 0.25 = 25%.

        Returns:
            OperatingCostResult with per-feature stats and portfolio totals.
        """
        features = [
            features_by_key[k] for k in self._sorted_keys(features_by_key)
        ]  # pragma: no cover - defensive
        return self._simulator.simulate_operating_costs(  # type: ignore[return-value]  # pragma: no cover - defensive
            features,
            cost_inflation_max=cost_inflation_max,
            scenarios=self.scenarios,
        )

    def portfolio_pl_variants(
        self,
        year1_results: Mapping[str, FeatureYear1Result],
        portfolio: PortfolioSnapshot,
    ) -> PortfolioPLVariants:
        """Portfolio P&L variant view: 4 BV statistics × 2 cost variants.

        Rows (business value statistics):
          Best (P95), Mean (Expected), Floor (BVF 95%), Tail (CVaR 95%)

        Variants:
          V1 (cash-flow): BV − total_investment − total_annual_opex
          V2 (P&L):       BV − total_annual_installment − total_annual_opex

        Args:
            year1_results: Year-1 simulation results keyed by feature key.
            portfolio: Aggregated portfolio snapshot (expected, var_95, cvar_95).

        Returns:
            PortfolioPLVariants with rows and cost totals.
        """
        keys = self._sorted_keys(year1_results)

        total_investment = float(
            sum(year1_results[k].feature.development_cost for k in keys)
        )
        total_installment = float(
            sum(year1_results[k].feature.annual_installment for k in keys)
        )
        total_opex = float(
            sum(year1_results[k].feature.annual_operating_cost for k in keys)
        )

        # P95 upside: derived from combined scenarios array
        combined = np.sum([year1_results[k].scenarios_eur for k in keys], axis=0)
        p95_bv = float(np.percentile(combined, 95))

        stats = [
            ("Best (P95)", p95_bv),
            ("Mean (Expected)", portfolio.expected),
            ("Floor (BVF 95%)", portfolio.var_95),
            ("Tail (CVaR 95%)", portfolio.cvar_95),
        ]

        rows = tuple(
            PLVariantRow(
                label=label,
                bv=bv,
                v1_net=bv - total_investment - total_opex,
                v2_net=bv - total_installment - total_opex,
            )
            for label, bv in stats
        )

        return PortfolioPLVariants(
            rows=rows,
            total_investment=total_investment,
            total_annual_installment=total_installment,
            total_annual_opex=total_opex,
        )

    def capital_budgeting_context(
        self,
        scenario: Any,
        *,
        years: int = 3,
    ) -> CapitalBudgetingContext:
        """Orchestrate all NB 03 simulations and KPIs in one call.

        Moves orchestration out of the notebook setup cell into the Application
        Layer, keeping the Presentation Layer (notebook) thin.

        Args:
            scenario: Loaded scenario from ``notebook_setup()``.
            years:    Number of projection years (default 3).

        Returns:
            :class:`CapitalBudgetingContext` with every result ready to display.
        """
        fbk = scenario.features_by_key  # pragma: no cover - defensive
        dr = scenario.discount_rate  # pragma: no cover - defensive
        # pragma: no cover - defensive
        year1 = self.simulate_year1(fbk)  # pragma: no cover - defensive
        portfolio_overview = self.portfolio_year1(year1)  # pragma: no cover - defensive
        # pragma: no cover - defensive
        multi_year = self.simulate_multi_year(
            fbk, discount_rate=dr, years=years
        )  # pragma: no cover - defensive
        portfolio_myr = self.combine_multi_year_results(  # pragma: no cover - defensive
            multi_year,
            discount_rate=dr,
            name=PORTFOLIO_TOTAL_NAME,  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        # pragma: no cover - defensive
        total_cost = self.total_investment(fbk)  # pragma: no cover - defensive
        total_annual_opex = self.total_annual_opex(fbk)  # pragma: no cover - defensive
        total_annual_installment = float(  # pragma: no cover - defensive
            sum(
                f.annual_installment for f in fbk.values()
            )  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        total_installment_years = int(
            max(f.installment_years for f in fbk.values())
        )  # pragma: no cover - defensive
        # pragma: no cover - defensive
        portfolio_myr_net = (
            self.net_multi_year_scenarios(  # pragma: no cover - defensive
                portfolio_myr,
                total_annual_opex,  # pragma: no cover - defensive
            )
        )  # pragma: no cover - defensive
        portfolio_npv_a = self.portfolio_npv(
            portfolio_myr_net, total_cost, dr
        )  # pragma: no cover - defensive
        portfolio_npv_b = (
            self.portfolio_npv_installment(  # pragma: no cover - defensive
                portfolio_myr,
                fbk,
                total_annual_opex,
                dr,
                years,  # pragma: no cover - defensive
            )
        )  # pragma: no cover - defensive
        portfolio_irr_a = self.portfolio_irr(
            portfolio_myr_net, total_cost
        )  # pragma: no cover - defensive
        portfolio_irr_b = (
            self.portfolio_irr_installment(  # pragma: no cover - defensive
                portfolio_myr,
                fbk,
                total_annual_opex,
                years,  # pragma: no cover - defensive
            )
        )  # pragma: no cover - defensive
        pi_a, pi_b = self.portfolio_profitability_index(  # pragma: no cover - defensive
            portfolio_npv_a,
            portfolio_npv_b,
            fbk,
            total_cost,
            dr,
            years=years,  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        npv_a_assessment = self.assess_portfolio_npv(
            portfolio_npv_a
        )  # pragma: no cover - defensive
        feat_sched_a, feat_sched_b = (
            self.feature_cashflow_schedules(  # pragma: no cover - defensive
                multi_year,
                fbk,
                dr,  # pragma: no cover - defensive
            )
        )  # pragma: no cover - defensive
        # pragma: no cover - defensive
        return CapitalBudgetingContext(  # pragma: no cover - defensive
            features_by_key=fbk,
            discount_rate=dr,
            scenarios=self.scenarios,
            year1=year1,
            portfolio_overview=portfolio_overview,
            multi_year=multi_year,
            portfolio_myr=portfolio_myr,
            total_cost=total_cost,
            total_annual_opex=total_annual_opex,
            total_annual_installment=total_annual_installment,
            total_installment_years=total_installment_years,
            portfolio_npv_a=portfolio_npv_a,
            portfolio_npv_b=portfolio_npv_b,
            portfolio_irr_a=portfolio_irr_a,
            portfolio_irr_b=portfolio_irr_b,
            pi_a=pi_a,
            pi_b=pi_b,
            npv_a_assessment=npv_a_assessment,
            feat_sched_a=feat_sched_a,
            feat_sched_b=feat_sched_b,
        )


@dataclass(frozen=True)
class CapitalBudgetingContext:
    """Aggregated NB 03 KPI bundle produced by ``capital_budgeting_context()``.

    Attributes
    ----------
    features_by_key:
        Feature definitions keyed by scenario key.
    discount_rate:
        Hurdle / discount rate used throughout.
    scenarios:
        Number of Monte Carlo scenarios.
    year1:
        Per-feature Year-1 simulation results.
    portfolio_overview:
        Aggregated Year-1 portfolio statistics.
    multi_year:
        Per-feature multi-year simulation results.
    portfolio_myr:
        Combined portfolio multi-year result.
    total_cost:
        Sum of all development costs (Option A investment).
    total_annual_opex:
        Sum of annual operating costs across all features.
    total_annual_installment:
        Year-1 portfolio installment total (display convenience).
    total_installment_years:
        Maximum installment window across all features (display convenience).
    portfolio_npv_a:
        Portfolio NPV under upfront financing (Option A).
    portfolio_npv_b:
        Portfolio NPV under installment financing (Option B).
    portfolio_irr_a:
        Portfolio IRR under Option A.
    portfolio_irr_b:
        Portfolio IRR under Option B (NaN when all cashflows positive).
    pi_a:
        Profitability Index = NPV_A / dev_cost for Option A.
    pi_b:
        Profitability Index = NPV_B / PV(installments) for Option B.
    npv_a_assessment:
        GO / CAUTION verdict based on NPV_A expected and floor.
    feat_sched_a:
        Per-feature cashflow schedule for Option A (tables and charts).
    feat_sched_b:
        Per-feature cashflow schedule for Option B.
    """

    features_by_key: Mapping[str, Feature]
    discount_rate: float
    scenarios: int
    year1: Any
    portfolio_overview: Any
    multi_year: Mapping[str, MultiYearResult]
    portfolio_myr: MultiYearResult
    total_cost: float
    total_annual_opex: float
    total_annual_installment: float
    total_installment_years: int
    portfolio_npv_a: Any  # NpvSummary
    portfolio_npv_b: Any  # NpvSummary
    portfolio_irr_a: Any  # IrrSummary
    portfolio_irr_b: Any  # IrrSummary
    pi_a: float
    pi_b: float
    npv_a_assessment: Any
    feat_sched_a: dict
    feat_sched_b: dict

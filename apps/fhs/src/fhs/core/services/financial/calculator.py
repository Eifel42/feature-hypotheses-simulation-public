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

"""Financial Calculator — time-value-of-money domain service.

All financial aggregate calculations for multi-year scenarios live here.
The ``MultiYearResult`` value object is a pure data container.

NPV formula is equivalent to ``numpy_financial.npv`` but vectorised
for 100 k+ scenario paths (~500× faster).  Equivalence is verified in
``test_matches_numpy_financial_npv``.

IRR uses ``numpy_financial.irr`` (standard implementation).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

try:
    import numpy_financial as npf
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    npf = None

_root_scalar: Any = None
try:
    from scipy.optimize import root_scalar as _scipy_root_scalar

    _root_scalar = _scipy_root_scalar
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    pass

root_scalar: Any = _root_scalar

if TYPE_CHECKING:
    from fhs.core.model.value_objects.financial_view import (
        FinancialViewResult,
        IrrAssessment,
        IrrSummary,
        NpvAssessment,
        NpvSummary,
    )
    from fhs.core.model.value_objects.multi_year_result import MultiYearResult


def discount_cashflows(
    yearly_scenarios: list[np.ndarray],
    discount_rate: float,
) -> np.ndarray:
    """Discount yearly scenario arrays to present value.

    Uses numpy broadcasting — same formula as ``numpy_financial.npv``:

        ``NPV = sum( cashflow_t / (1 + rate)^t )``

    Equivalence with ``npf.npv`` is verified in
    ``test_matches_numpy_financial_npv``.

    Args:
        yearly_scenarios: One array per year (all same length).
                          Index 0 → Year 1, index 1 → Year 2, etc.
        discount_rate: Annual discount rate (e.g. 0.10 for 10 %).

    Returns:
        1-D array of NPV values (one per scenario path).
    """
    if not yearly_scenarios:
        return np.array([])
    stacked = np.stack(yearly_scenarios)  # (n_years, n_scenarios)
    years = np.arange(1, len(yearly_scenarios) + 1)
    factors = (1 + discount_rate) ** years  # (n_years,)
    return np.asarray((stacked / factors[:, np.newaxis]).sum(axis=0), dtype=float)


class FinancialCalculator:
    """Stateless domain service for financial mathematics."""

    # ── Low-level: raw arrays ────────────────────────────────────────

    @staticmethod
    def npv(
        yearly_scenarios: list[np.ndarray],
        discount_rate: float,
    ) -> np.ndarray:
        """NPV per scenario path from raw yearly arrays."""
        return discount_cashflows(yearly_scenarios, discount_rate)

    @staticmethod
    def npv_metrics(
        yearly_scenarios: list[np.ndarray],
        discount_rate: float,
    ) -> NpvSummary:
        """NPV summary statistics (expected, var_95, p95, std)."""
        from ...model.value_objects import NpvSummary

        npv_arr = discount_cashflows(yearly_scenarios, discount_rate)
        if len(npv_arr) == 0:
            return NpvSummary(expected=0.0, var_95=0.0, p95=0.0, std=0.0)
        return NpvSummary(
            expected=float(np.mean(npv_arr)),
            var_95=float(np.percentile(npv_arr, 5)),
            p95=float(np.percentile(npv_arr, 95)),
            std=float(np.std(npv_arr)),
        )

    @staticmethod
    def cumulative_scenarios(yearly_scenarios: list[np.ndarray]) -> np.ndarray:
        """Undiscounted sum of all yearly scenario arrays."""
        if not yearly_scenarios:
            return np.array([])  # pragma: no cover - defensive
        return np.asarray(np.sum(yearly_scenarios, axis=0), dtype=float)

    @staticmethod
    def cumulative_metrics(
        yearly_scenarios: list[np.ndarray],
    ) -> NpvSummary:
        """3-year cumulative summary (expected, var_95, p95, std)."""
        from ...model.value_objects import NpvSummary

        cum = FinancialCalculator.cumulative_scenarios(
            yearly_scenarios
        )  # pragma: no cover - defensive
        if len(cum) == 0:  # pragma: no cover - defensive
            return NpvSummary(
                expected=0.0, var_95=0.0, p95=0.0, std=0.0
            )  # pragma: no cover - defensive
        return NpvSummary(  # pragma: no cover - defensive
            expected=float(np.mean(cum)),
            var_95=float(np.percentile(cum, 5)),
            p95=float(np.percentile(cum, 95)),
            std=float(np.std(cum)),
        )

    # ── IRR (Internal Rate of Return) ────────────────────────────────

    @staticmethod
    def irr(
        initial_investment: float,
        yearly_cashflows: list[float],
    ) -> float:
        """IRR from a single cashflow series using ``numpy_financial.irr``.

        Args:
            initial_investment: Upfront cost (positive number, e.g. 150_000).
            yearly_cashflows: Expected cashflow per year [year1, year2, ...].

        Returns:
            IRR as a decimal (e.g. 0.25 = 25 %).  Returns NaN if no
            solution exists (e.g. all cashflows negative).
        """
        cf = [-initial_investment, *list(yearly_cashflows)]

        if not any(c > 0 for c in cf) or not any(c < 0 for c in cf):
            return float("nan")

        if npf is not None:
            result = npf.irr(cf)
            if np.isfinite(result):
                return float(result)
            # npf.irr fails for negative IRRs; bisection finds them
        return _irr_bisection(cf)  # pragma: no cover - scipy fallback

    @staticmethod
    def irr_from_scenarios(
        initial_investment: float,
        yearly_scenarios: list[np.ndarray],
    ) -> IrrSummary:
        """IRR summary from Monte Carlo scenario arrays.

        Computes IRR of the *expected* (mean) cashflow per year.
        This is the most meaningful single IRR for board decisions.

        Also computes IRR of the floor (5th pctl) and ceiling (95th pctl)
        cashflow paths to show the range.

        Args:
            initial_investment: Upfront cost (positive number).
            yearly_scenarios: One array per year (100k scenarios each).

        Returns:
            IrrSummary with expected, floor, ceiling IRR values.
        """
        from ...model.value_objects import IrrSummary

        if not yearly_scenarios:
            return IrrSummary(
                expected=float("nan"),
                floor=float("nan"),
                ceiling=float("nan"),
            )

        expected_cf = [float(np.mean(y)) for y in yearly_scenarios]
        floor_cf = [float(np.percentile(y, 5)) for y in yearly_scenarios]
        ceiling_cf = [float(np.percentile(y, 95)) for y in yearly_scenarios]

        return IrrSummary(
            expected=FinancialCalculator.irr(initial_investment, expected_cf),
            floor=FinancialCalculator.irr(initial_investment, floor_cf),
            ceiling=FinancialCalculator.irr(initial_investment, ceiling_cf),
        )

    # ── High-level: MultiYearResult convenience ──────────────────────

    @staticmethod
    def _yearly(result: MultiYearResult) -> list[np.ndarray]:
        return [y.scenarios for y in result.years]

    @staticmethod
    def result_npv_scenarios(result: MultiYearResult) -> np.ndarray:
        """NPV per scenario path for a MultiYearResult."""
        return discount_cashflows(
            FinancialCalculator._yearly(result), result.discount_rate
        )

    @staticmethod
    def result_npv_expected(result: MultiYearResult) -> float:
        npv = FinancialCalculator.result_npv_scenarios(result)
        return float(np.mean(npv)) if len(npv) > 0 else 0.0

    @staticmethod
    def result_npv_var_95(result: MultiYearResult) -> float:
        npv = FinancialCalculator.result_npv_scenarios(result)
        return float(np.percentile(npv, 5)) if len(npv) > 0 else 0.0

    @staticmethod
    def result_npv_p95(result: MultiYearResult) -> float:
        npv = FinancialCalculator.result_npv_scenarios(result)
        return float(np.percentile(npv, 95)) if len(npv) > 0 else 0.0

    @staticmethod
    def result_total_3y_expected(result: MultiYearResult) -> float:
        return sum(y.expected for y in result.years)

    @staticmethod
    def result_total_3y_var_95(result: MultiYearResult) -> float:
        cum = FinancialCalculator.cumulative_scenarios(
            FinancialCalculator._yearly(result)
        )
        return float(np.percentile(cum, 5)) if len(cum) > 0 else 0.0

    @staticmethod
    def result_total_3y_p95(result: MultiYearResult) -> float:
        cum = FinancialCalculator.cumulative_scenarios(
            FinancialCalculator._yearly(result)
        )
        return float(np.percentile(cum, 95)) if len(cum) > 0 else 0.0

    @staticmethod
    def result_irr(result: MultiYearResult, investment: float) -> IrrSummary:
        """IRR summary for a MultiYearResult (convenience wrapper)."""
        return FinancialCalculator.irr_from_scenarios(
            investment, FinancialCalculator._yearly(result)
        )

    @staticmethod
    def assess_irr(
        irr_result: IrrSummary,
        discount_rate: float,
        *,
        near_break_even_band: float = 0.02,
    ) -> IrrAssessment:
        """Assess IRR against hurdle rate with a typed decision result."""
        from ...model.value_objects import IrrAssessment

        expected_irr = float(irr_result.expected)
        floor_irr = float(irr_result.floor)
        margin = expected_irr - float(discount_rate)

        if expected_irr > discount_rate:
            verdict = "GO"
            primary_message = (
                f"Portfolio IRR ({expected_irr:.0%}) exceeds cost of capital "
                f"({discount_rate:.0%}) by {margin:.0%}. Investment creates value."
            )
        elif abs(margin) < near_break_even_band:
            verdict = "CONDITIONAL_GO"
            primary_message = (
                f"Portfolio IRR ({expected_irr:.0%}) is near break-even "
                f"({discount_rate:.0%}). Review assumptions or reduce costs."
            )
        else:
            verdict = "REVIEW"
            primary_message = (
                f"Portfolio IRR ({expected_irr:.0%}) is below cost of capital "
                f"({discount_rate:.0%}). Reconsider the investment."
            )

        downside_message = None
        if floor_irr < discount_rate:  # pragma: no cover - partial branch
            downside_message = (
                f"However, IRR Floor ({floor_irr:.0%}) is below cost of capital. "
                "There is downside risk in worst-case scenarios."
            )

        return IrrAssessment(
            verdict=verdict,
            primary_message=primary_message,
            downside_message=downside_message,
            margin_to_discount_rate=margin,
            expected_above_hurdle=expected_irr > discount_rate,
            downside_below_hurdle=floor_irr < discount_rate,
        )

    @staticmethod
    def result_npv(
        result: MultiYearResult, investment: float, discount_rate: float
    ) -> NpvSummary:
        """NPV summary for a MultiYearResult minus upfront investment.

        Computes NPV for expected, var_95, p95, and std,
        then subtracts the upfront investment cost.

        Args:
            result: Multi-year simulation result
            investment: Upfront investment cost (positive number)
            discount_rate: Annual discount rate (e.g., 0.10 for 10%)

        Returns:
            NpvSummary with expected, var_95, p95, std
        """
        from ...model.value_objects import NpvSummary

        yearly = FinancialCalculator._yearly(result)
        if not yearly:
            return NpvSummary(  # pragma: no cover - defensive
                expected=-investment,
                var_95=-investment,
                p95=-investment,
                std=0.0,
            )

        # Calculate NPV for all scenarios
        npv_scenarios = discount_cashflows(yearly, discount_rate)

        # Subtract investment from each
        npv_scenarios_net = npv_scenarios - investment

        return NpvSummary(
            expected=float(np.mean(npv_scenarios_net)),
            var_95=float(np.percentile(npv_scenarios_net, 5)),
            p95=float(np.percentile(npv_scenarios_net, 95)),
            std=float(np.std(npv_scenarios_net)),
        )

    @staticmethod
    def assess_npv(npv_result: NpvSummary) -> NpvAssessment:
        """Assess NPV expected/floor values with a typed decision result."""
        from ...model.value_objects import NpvAssessment

        expected_npv = float(npv_result.expected)
        floor_npv = float(npv_result.var_95)

        if expected_npv > 0:
            verdict = "GO"
            primary_message = (
                f"Portfolio NPV is positive (€{expected_npv:,.0f}). "
                "The investment creates value."
            )
        else:
            verdict = "REVIEW"
            primary_message = (
                f"Portfolio NPV is negative (€{expected_npv:,.0f}). "
                "Reconsider the investment or reduce costs."
            )

        downside_message = None
        if floor_npv < 0 < expected_npv:
            downside_message = (
                f"However, NPV Floor is negative (€{floor_npv:,.0f}). "
                "There is downside risk in worst-case scenarios."
            )

        return NpvAssessment(
            verdict=verdict,
            primary_message=primary_message,
            downside_message=downside_message,
            positive_expected=expected_npv > 0,
            downside_risk=floor_npv < 0,
        )

    @staticmethod
    def result_npv_installment(
        result: MultiYearResult,
        annual_installment: float,
        installment_years: int,
        discount_rate: float,
    ) -> NpvSummary:
        """NPV under installment financing — first payment in Year 0.

        Deducts ``annual_installment`` at t=0 (development year) and from
        scenario cash flows in years 1 through ``installment_years − 1``.
        Total installments = ``installment_years``, window [0, n-1].

        Formula::

            NPV_B = −Inst
                  + Σ_{t=1}^{n−1} (cf_t − Inst)/(1+r)^t
                  + Σ_{t=n}^{T}   cf_t/(1+r)^t

        where cf_t already has annual OpEx deducted.

        Args:
            result: Multi-year simulation result (OpEx already deducted).
            annual_installment: Annual installment amount (``C_dev / n``).
            installment_years: Number of years over which installments are paid.
            discount_rate: Annual discount rate (e.g. 0.08 for 8 %).
        """
        from ...model.value_objects import NpvSummary

        yearly = FinancialCalculator._yearly(result)
        if not yearly:
            return NpvSummary(expected=0.0, var_95=0.0, p95=0.0, std=0.0)

        adjusted = []
        for i, yr_scenarios in enumerate(yearly):
            year_num = i + 1  # 1-indexed
            if year_num < installment_years:
                adjusted.append(yr_scenarios - annual_installment)
            else:
                adjusted.append(yr_scenarios)

        # Year 0 installment: discount factor = 1.0, subtract directly
        npv_scenarios = discount_cashflows(adjusted, discount_rate) - annual_installment
        return NpvSummary(
            expected=float(np.mean(npv_scenarios)),
            var_95=float(np.percentile(npv_scenarios, 5)),
            p95=float(np.percentile(npv_scenarios, 95)),
            std=float(np.std(npv_scenarios)),
        )

    @staticmethod
    def result_npv_installment_schedule(
        result: MultiYearResult,
        per_year_installments: list[float],
        discount_rate: float,
        year0_installment: float = 0.0,
    ) -> NpvSummary:
        """NPV under installment financing with an explicit per-year schedule.

        More accurate than :meth:`result_npv_installment` when features have
        different ``installment_years`` — deducts the exact portfolio installment
        for each year rather than a flat amount.

        Args:
            result: Multi-year simulation result (OpEx already deducted).
            per_year_installments: Installment amounts for years 1..n, e.g.
                ``[60_000, 25_000]`` when year-2 has only one feature left.
            discount_rate: Annual discount rate (e.g. 0.08 for 8 %).
            year0_installment: Installment paid at t=0 (discount factor = 1.0).
        """
        from ...model.value_objects import NpvSummary

        yearly = FinancialCalculator._yearly(result)
        if not yearly:
            return NpvSummary(
                expected=0.0, var_95=0.0, p95=0.0, std=0.0
            )  # pragma: no cover - defensive

        adjusted = [
            yr - (per_year_installments[i] if i < len(per_year_installments) else 0.0)
            for i, yr in enumerate(yearly)
        ]
        npv_scenarios = discount_cashflows(adjusted, discount_rate) - year0_installment
        return NpvSummary(
            expected=float(np.mean(npv_scenarios)),
            var_95=float(np.percentile(npv_scenarios, 5)),
            p95=float(np.percentile(npv_scenarios, 95)),
            std=float(np.std(npv_scenarios)),
        )

    @staticmethod
    def irr_installment_schedule(
        per_year_installments: list[float],
        yearly_cashflows: list[float],
        year0_installment: float = 0.0,
    ) -> float:
        """IRR under installment financing with an explicit per-year schedule.

        Companion to :meth:`irr_installment` for portfolios where features
        have different installment windows.  Returns NaN when all cashflows
        are non-negative (no sign change → IRR is undefined).

        Args:
            per_year_installments: Installment due in years 1..n (index 0 = year 1).
            yearly_cashflows: Net cashflows per year (OpEx already deducted).
            year0_installment: Installment paid at t=0 (anchors the series).
        """
        adjusted = [
            cf - (per_year_installments[i] if i < len(per_year_installments) else 0.0)
            for i, cf in enumerate(yearly_cashflows)
        ]
        cf_series = [-year0_installment, *adjusted]

        if not any(c > 0 for c in cf_series) or not any(c < 0 for c in cf_series):
            return float("nan")  # pragma: no cover - scipy fallback

        if npf is not None:
            result = npf.irr(cf_series)
            if np.isfinite(result):
                return float(result)
            # npf.irr fails for negative IRRs; bisection finds them
        return _irr_bisection(cf_series)  # pragma: no cover - scipy fallback

    @staticmethod
    # noinspection PyTypeHintsInspection
    def irr_installment_from_scenarios_schedule(
        per_year_installments: list[float],
        yearly_scenarios: list[np.ndarray],
        year0_installment: float = 0.0,
    ) -> IrrSummary:
        """IRR under installment financing (schedule variant) from Monte Carlo scenarios.

        Uses expected, 5th-pctl, and 95th-pctl cashflow paths.

        Args:
            per_year_installments: Installment due in years 1..n (index 0 = year 1).
            yearly_scenarios: Monte Carlo scenario arrays per year.
            year0_installment: Installment paid at t=0 (anchors the series).
        """
        from ...model.value_objects import IrrSummary

        if not yearly_scenarios:
            return IrrSummary(  # pragma: no cover - scipy fallback
                expected=float("nan"), floor=float("nan"), ceiling=float("nan")
            )

        expected_cf = [float(np.mean(y)) for y in yearly_scenarios]
        floor_cf = [float(np.percentile(y, 5)) for y in yearly_scenarios]
        ceiling_cf = [float(np.percentile(y, 95)) for y in yearly_scenarios]

        return IrrSummary(
            expected=FinancialCalculator.irr_installment_schedule(
                per_year_installments, expected_cf, year0_installment
            ),
            floor=FinancialCalculator.irr_installment_schedule(
                per_year_installments, floor_cf, year0_installment
            ),
            ceiling=FinancialCalculator.irr_installment_schedule(
                per_year_installments, ceiling_cf, year0_installment
            ),
        )

    @staticmethod
    def irr_installment(
        annual_installment: float,
        installment_years: int,
        yearly_cashflows: list[float],
    ) -> float:
        """IRR under installment financing — first payment at Year 0.

        Installments span [0, installment_years − 1]: t=0 is the Year-0
        anchor, years 1..(n-1) also carry installments, year n onward are free.
        Returns NaN when all cashflows are non-negative (no sign change).
        """
        adjusted = [
            cf - annual_installment if (i + 1) < installment_years else cf
            for i, cf in enumerate(yearly_cashflows)
        ]
        cf_series = [-annual_installment, *adjusted]  # Year 0 first payment

        if not any(c > 0 for c in cf_series) or not any(c < 0 for c in cf_series):
            return float("nan")

        if npf is not None:
            result = npf.irr(cf_series)
            if np.isfinite(result):
                return float(result)
            # npf.irr fails for negative IRRs; bisection finds them
        return _irr_bisection(cf_series)  # pragma: no cover - scipy fallback

    @staticmethod
    def irr_installment_from_scenarios(
        annual_installment: float,
        installment_years: int,
        yearly_scenarios: list[np.ndarray],
    ) -> IrrSummary:
        """IRR under installment financing from Monte Carlo scenarios.

        Uses the expected, 5th-pctl, and 95th-pctl cashflow paths.
        Values may be NaN when no sign change exists (all cashflows positive).
        """
        from ...model.value_objects import IrrSummary

        if not yearly_scenarios:
            return IrrSummary(
                expected=float("nan"),
                floor=float("nan"),
                ceiling=float("nan"),
            )

        expected_cf = [float(np.mean(y)) for y in yearly_scenarios]
        floor_cf = [float(np.percentile(y, 5)) for y in yearly_scenarios]
        ceiling_cf = [float(np.percentile(y, 95)) for y in yearly_scenarios]

        return IrrSummary(
            expected=FinancialCalculator.irr_installment(
                annual_installment, installment_years, expected_cf
            ),
            floor=FinancialCalculator.irr_installment(
                annual_installment, installment_years, floor_cf
            ),
            ceiling=FinancialCalculator.irr_installment(
                annual_installment, installment_years, ceiling_cf
            ),
        )

    @staticmethod
    def result_financial_view(
        result: MultiYearResult,
        *,
        investment: float,
        discount_rate: float,
    ) -> FinancialViewResult:
        """Assemble combined NPV/IRR/3Y financial view for a multi-year result."""
        from ...model.value_objects import FinancialViewResult

        npv = FinancialCalculator.result_npv(result, investment, discount_rate)
        irr = FinancialCalculator.result_irr(result, investment)
        return FinancialViewResult(
            npv_expected=npv.expected,
            npv_floor=npv.var_95,
            npv_ceiling=npv.p95,
            irr_expected=irr.expected,
            irr_floor=irr.floor,
            irr_ceiling=irr.ceiling,
            total_3y_expected=FinancialCalculator.result_total_3y_expected(result),
            total_3y_floor=FinancialCalculator.result_total_3y_var_95(result),
        )


def _find_irr_bracket(
    cashflows: list[float],
    npv_fn: Any,
) -> tuple[float, float, float, float] | None:
    if len(cashflows) < 2:  # pragma: no cover - scipy fallback
        return None  # pragma: no cover - scipy fallback
    # pragma: no cover - scipy fallback
    if not any(cf > 0 for cf in cashflows) or not any(
        cf < 0 for cf in cashflows
    ):  # pragma: no cover - scipy fallback
        return None  # pragma: no cover - scipy fallback
    # pragma: no cover - scipy fallback
    low = -0.9999  # pragma: no cover - scipy fallback
    f_low = npv_fn(low)  # pragma: no cover - scipy fallback
    for candidate_high in (
        10.0,
        25.0,
        50.0,
        100.0,
    ):  # pragma: no cover - scipy fallback
        candidate_f_high = npv_fn(candidate_high)  # pragma: no cover - scipy fallback
        if f_low * candidate_f_high <= 0:  # pragma: no cover - scipy fallback
            return (
                low,
                candidate_high,
                f_low,
                candidate_f_high,
            )  # pragma: no cover - scipy fallback
    return None  # pragma: no cover - scipy fallback


def _bisect_irr_root(npv_fn: Any, low: float, high: float, f_low: float) -> float:
    for _ in range(200):  # pragma: no cover - scipy fallback
        mid = (low + high) / 2.0  # pragma: no cover - scipy fallback
        f_mid = npv_fn(mid)  # pragma: no cover - scipy fallback
        if abs(f_mid) < 1e-9:  # pragma: no cover - scipy fallback
            return mid  # pragma: no cover - scipy fallback
        if f_low * f_mid < 0:  # pragma: no cover - scipy fallback
            high = mid  # pragma: no cover - scipy fallback
        else:  # pragma: no cover - scipy fallback
            low = mid  # pragma: no cover - scipy fallback
            f_low = f_mid  # pragma: no cover - scipy fallback
    return (low + high) / 2.0  # pragma: no cover - scipy fallback


def _irr_bisection(cashflows: list[float]) -> float:
    """Fallback IRR solver when numpy_financial is unavailable."""

    def _npv(rate: float) -> float:  # pragma: no cover - scipy fallback
        return sum(
            cf / ((1.0 + rate) ** idx) for idx, cf in enumerate(cashflows)
        )  # pragma: no cover - scipy fallback

    # pragma: no cover - scipy fallback
    bracket = _find_irr_bracket(cashflows, _npv)  # pragma: no cover - scipy fallback
    if bracket is None:  # pragma: no cover - scipy fallback
        return float("nan")  # pragma: no cover - scipy fallback
    low, high, f_low, f_high = bracket  # pragma: no cover - scipy fallback
    # pragma: no cover - scipy fallback
    if f_low == 0:  # pragma: no cover - scipy fallback
        return low  # pragma: no cover - scipy fallback
    if f_high == 0:  # pragma: no cover - scipy fallback
        return high  # pragma: no cover - scipy fallback
    # pragma: no cover - scipy fallback
    if root_scalar is not None:  # pragma: no cover - scipy fallback
        try:  # pragma: no cover - scipy fallback
            # noinspection PyCallingNonCallableInspection  # pragma: no cover - scipy fallback
            solution = root_scalar(  # pragma: no cover - scipy fallback
                _npv,  # pragma: no cover - scipy fallback
                method="brentq",  # pragma: no cover - scipy fallback
                bracket=(low, high),  # pragma: no cover - scipy fallback
                xtol=1e-9,  # pragma: no cover - scipy fallback
                rtol=1e-9,  # pragma: no cover - scipy fallback
                maxiter=200,  # pragma: no cover - scipy fallback
            )  # pragma: no cover - scipy fallback
            if solution.converged:  # pragma: no cover - scipy fallback
                return float(solution.root)  # pragma: no cover - scipy fallback
        except ValueError:  # pragma: no cover - scipy fallback
            return float("nan")  # pragma: no cover - scipy fallback
    # pragma: no cover - scipy fallback
    return _bisect_irr_root(_npv, low, high, f_low)  # pragma: no cover - scipy fallback

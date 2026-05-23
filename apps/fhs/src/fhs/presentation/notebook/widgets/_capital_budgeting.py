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

"""Capital budgeting methods."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fhs.core.model.value_objects import PortfolioPLVariants

from ..styling import COLORS as _COLORS
from ._capital_budgeting_formatters import (
    format_cashflow,
    format_discount_factor,
    format_irr_badge,
    format_irr_verdict,
    format_npv,
    format_value_k,
)
from ._helpers import _cell_color, _eur, _fmt_signed


def _y1_net_html(value: float, colors: Any = _COLORS) -> str:
    sign = "+" if value >= 0 else "−"
    color = colors.success if value >= 0 else colors.danger
    return (
        f"<span class='fhs-y1-net' style='color:{color};'>"
        f"{sign}€{abs(value):,.0f}</span>"
    )


def _y1_amount_html(
    value: float,
    color: str | None = None,
) -> str:
    color_style = f"color:{color};" if color else ""
    return f"<span class='fhs-y1-amount' style='{color_style}'>{_eur(value)}</span>"


def _y1_stack_html(label: str, value: str, tone: str | None = None) -> str:
    tone_style = f"color:{tone};" if tone else ""
    return (
        "<div class='fhs-y1-stack-row'>"
        f"<span class='fhs-y1-stack-label'>{label}</span>"
        f"<span class='fhs-y1-stack-value' style='{tone_style}'>{value}</span>"
        "</div>"
    )


def _y1_relief_html(v1: float, v2: float, colors: Any = _COLORS) -> str:
    relief = v2 - v1
    color = colors.success if relief >= 0 else colors.danger
    sign = "+" if relief >= 0 else "−"
    label = "B improves Year 1" if relief >= 0 else "A improves Year 1"
    return (
        f"<div class='fhs-y1-signal' style='border-color:{color};'>"
        f"<span class='fhs-y1-signal-main' style='color:{color};'>"
        f"{sign}€{abs(relief):,.0f}</span>"
        f"<span class='fhs-y1-signal-label'>{label}</span>"
        "</div>"
    )


def _y1_row_background(
    index: int,
    is_total: bool,
    colors: Any = _COLORS,
) -> str:
    if is_total:
        return colors.success_surface
    return colors.surface if index % 2 == 0 else colors.background


def _npv_summary_card(
    label: str,
    value: str,
    color: str,
    background: str,
    colors: Any = _COLORS,
) -> str:
    return (
        f"<div style='flex:1;min-width:185px;background:{background};"
        f"border:1px solid {colors.border};border-top:4px solid {color};"
        f"border-radius:8px;padding:12px 14px'>"
        f"<div style='font-size:11px;font-weight:800;color:{colors.subtle};"
        f"text-transform:uppercase;letter-spacing:0.04em'>{label}</div>"
        f"<div style='font-size:24px;font-weight:850;color:{color};"
        f"line-height:1.1;margin-top:5px'>{value}</div>"
        f"</div>"
    )


def _npv_benefit_background(benefit: float, colors: Any = _COLORS) -> str:
    return colors.success_surface if benefit >= 0 else colors.danger_surface


def _irr_comparison_panel(
    irr_rows: list | None,
    irr_map_a: dict[str, float],
    irr_map_b: dict[str, float],
    hurdle: float,
    portfolio_irr_a: float | None,
    portfolio_irr_b: float | None,
    feat_names: list[str],
    pf_name: str,
) -> str:
    if not irr_rows:
        return ""
    th = (
        f"<tr style='background:{_COLORS.neutral};color:{_COLORS.background}'>"
        f"<th style='padding:8px 14px;text-align:left;min-width:170px'>Hypothesis</th>"
        f"<th style='padding:8px 14px;text-align:center;min-width:120px'>IRR — Option A</th>"
        f"<th style='padding:8px 14px;text-align:center;min-width:120px'>IRR — Option B</th>"
        f"<th style='padding:8px 14px;text-align:left;min-width:200px'>Verdict</th>"
        f"</tr>"
    )
    body = th
    for i, name in enumerate(feat_names):
        bg = _COLORS.surface if i % 2 == 0 else _COLORS.background
        a_val = irr_map_a.get(name)
        b_val = irr_map_b.get(name)
        body += (
            f"<tr style='background:{bg}'>"
            f"<td style='padding:9px 14px;font-weight:600;font-size:13px'>{name}</td>"
            f"<td style='padding:9px 14px;text-align:center'>"
            f"{format_irr_badge(a_val, hurdle, colors=_COLORS)}</td>"
            f"<td style='padding:9px 14px;text-align:center'>"
            f"{format_irr_badge(b_val, hurdle, colors=_COLORS)}</td>"
            f"<td style='padding:9px 14px'>"
            f"{format_irr_verdict(a_val, b_val, hurdle, colors=_COLORS)}</td>"
            f"</tr>"
        )
    body += (
        f"<tr style='background:{_COLORS.surface};"
        f"border-top:3px solid {_COLORS.neutral}'>"
        f"<td style='padding:10px 14px;font-weight:700;font-size:14px'>{pf_name}</td>"
        f"<td style='padding:10px 14px;text-align:center'>"
        f"{format_irr_badge(portfolio_irr_a, hurdle, colors=_COLORS)}</td>"
        f"<td style='padding:10px 14px;text-align:center'>"
        f"{format_irr_badge(portfolio_irr_b, hurdle, colors=_COLORS)}</td>"
        f"<td style='padding:10px 14px'>"
        f"{format_irr_verdict(portfolio_irr_a, portfolio_irr_b, hurdle, colors=_COLORS)}</td>"
        f"</tr>"
    )
    hurdle_note = (
        f"Hurdle rate: {hurdle:.0%}. "
        f"Green = IRR ≥ hurdle · Red = IRR &lt; hurdle · "
        f"'≤ 0 % — no root' = NPV has no positive zero-crossing; "
        f"the investment does not break even at any positive rate."
    )
    return (
        f"<div style='border:1px solid {_COLORS.border};border-radius:10px;"
        f"overflow:auto;border-left:5px solid {_COLORS.neutral};margin:10px 0'>"
        f"<div style='background:{_COLORS.neutral};color:{_COLORS.background};"
        f"padding:9px 14px;font-weight:700;font-size:13px'>"
        f"IRR at a Glance — Option A vs. Option B</div>"
        f"<div style='overflow-x:auto'>"
        f"<table style='width:100%;border-collapse:collapse'>"
        f"{body}</table></div>"
        f"<div style='padding:5px 14px 8px;font-size:10px;"
        f"color:{_COLORS.neutral};border-top:1px solid {_COLORS.border}'>"
        f"{hurdle_note}</div>"
        f"</div>"
    )


def _render_cashflow_table(sched: dict, accent: str, _hurdle: float) -> str:
    years = sched["years"]
    dfs = sched["discount_factors"]
    rows = sched["rows"]
    portfolio = sched["portfolio"]
    inv_label = sched["inv_label"]

    year_labels = ["Year 0"] + [f"Year {y}" for y in years[1:]]

    hdr = (
        f"<tr style='background:{accent};color:{_COLORS.background}'>"
        f"<th style='padding:7px 12px;text-align:left;min-width:160px'>Feature</th>"
    )
    for yl in year_labels:
        hdr += f"<th style='padding:7px 12px;text-align:right;min-width:95px'>{yl}</th>"
    hdr += "<th style='padding:7px 12px;text-align:right;min-width:95px'>NPV</th></tr>"
    body = hdr

    for i, row in enumerate(rows):
        bg = _COLORS.surface if i % 2 == 0 else _COLORS.background
        body += (
            f"<tr style='background:{bg}'>"
            f"<td style='padding:6px 12px;font-size:13px;font-weight:600'>"
            f"{row['name']}</td>"
        )
        for cf in row["cashflows"]:
            body += (
                f"<td style='padding:6px 12px;text-align:right;font-size:13px'>"
                f"{format_cashflow(cf, colors=_COLORS)}</td>"
            )
        body += (
            f"<td style='padding:6px 12px;text-align:right;font-size:13px'>"
            f"{format_npv(row['npv'], colors=_COLORS)}</td>"
            f"</tr>"
        )

    body += (
        f"<tr style='background:{_COLORS.background};"
        f"border-top:1px solid {_COLORS.border}'>"
        f"<td style='padding:4px 12px;font-size:11px;color:{_COLORS.neutral}'>"
        f"Discount Factor</td>"
    )
    for df_val in dfs:
        body += (
            f"<td style='padding:4px 12px;text-align:right'>"
            f"{format_discount_factor(df_val, colors=_COLORS)}</td>"
        )
    body += (
        f"<td style='padding:4px 12px;text-align:right;"
        f"font-size:11px;color:{_COLORS.neutral}'>∑ PV</td>"
        f"</tr>"
    )

    pf = portfolio
    pf_npv_color = _COLORS.success if pf["npv"] >= 0 else _COLORS.danger
    pf_sign = "+" if pf["npv"] >= 0 else "−"
    body += (
        f"<tr style='background:{_COLORS.surface};border-top:3px solid {accent}'>"
        f"<td style='padding:9px 12px;font-weight:700;font-size:14px'>{pf['name']}</td>"
    )
    for cf in pf["cashflows"]:
        body += (
            f"<td style='padding:9px 12px;text-align:right;font-size:14px'>"
            f"{format_cashflow(cf, colors=_COLORS)}</td>"
        )
    body += (
        f"<td style='padding:9px 12px;text-align:right;"
        f"font-size:15px;font-weight:800;color:{pf_npv_color}'>"
        f"{pf_sign}€{abs(pf['npv']):,.0f}</td>"
        f"</tr>"
    )

    return (
        f"<div style='border:1px solid {_COLORS.border};border-radius:10px;"
        f"overflow:auto;border-left:5px solid {accent};margin:10px 0'>"
        f"<div style='background:{accent};color:{_COLORS.background};"
        f"padding:10px 14px;font-weight:700;font-size:14px'>"
        f"{sched['label']}</div>"
        f"<div style='padding:4px 12px;font-size:11px;color:{_COLORS.neutral};"
        f"background:{_COLORS.surface}'>{inv_label}</div>"
        f"<div style='overflow-x:auto'>"
        f"<table style='width:100%;border-collapse:collapse'>"
        f"{body}</table></div>"
        f"</div>"
    )


class _CapitalBudgetingMixin:
    # Host stubs for static typing; concrete implementations are provided by facade mixins.
    def __call__(self, html: str) -> None:  # pragma: no cover - typing stub
        del html

    def sensitivity(
        self,
        _rows: list[tuple[str, ...]],
        _headers: tuple[str, ...],
        **_kwargs: Any,
    ) -> None:  # pragma: no cover - typing stub
        return None

    def operating_costs(
        self, result: Any, title: str = "Operating Cost Simulation"
    ) -> None:
        """Display an OperatingCostResult as an HTML table.

        Shows per-feature base cost, expected cost (with average inflation),
        and worst-case cost (at maximum inflation). Includes portfolio totals.

        Parameters
        ----------
        result:
            ``OperatingCostResult`` object from
            ``BlockchainCaseStudyService.simulate_operating_costs()``.
        title:
            Card title.
        """
        from ..styling import COLORS

        hdr_bg = COLORS.primary
        hdr_fg = COLORS.background
        alt_bg = COLORS.surface

        rows_html = ""
        for i, (name, stats) in enumerate(result.per_feature.items()):
            bg = alt_bg if i % 2 == 0 else COLORS.background
            short = name.split(": ", 1)[-1] if ": " in name else name
            uplift = stats.cost_uplift_eur
            rows_html += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:6px 10px;font-weight:600'>{short}</td>"
                f"<td style='padding:6px 10px;text-align:right'>€{stats.base_annual_cost:,.0f}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.warning}'>"
                f"€{stats.expected_cost:,.0f}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.danger}'>"
                f"€{stats.worst_case_cost:,.0f}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-size:11px;"
                f"color:{COLORS.neutral}'>+€{uplift:,.0f} max</td>"
                f"</tr>"
            )

        # Portfolio totals row
        rows_html += (
            f"<tr style='border-top:2px solid {hdr_bg};background:{alt_bg}'>"
            f"<td style='padding:6px 10px;font-weight:700'>Portfolio Total</td>"
            f"<td style='padding:6px 10px;text-align:right;font-weight:700'>"
            f"€{result.portfolio_base_cost:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
            f"color:{COLORS.warning}'>€{result.portfolio_expected_cost:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
            f"color:{COLORS.danger}'>€{result.portfolio_worst_case_cost:,.0f}</td>"
            f"<td style='padding:6px 10px;text-align:right;font-size:11px;"
            f"color:{COLORS.neutral}'>"
            f"inflation max {result.inflation_max:.0%}</td>"
            f"</tr>"
        )

        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {hdr_bg};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
            f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
            f"text-align:left;font-weight:700;font-size:14px'>"
            f"💸 {title}"
            f"<span style='float:right;font-weight:400;font-size:11px'>"
            f"avg inflation ≈ {result.expected_inflation_pct:.1f}%</span></caption>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
            f"<th style='padding:6px 10px;text-align:left'>Feature</th>"
            f"<th style='padding:6px 10px;text-align:right'>Base (EUR/yr)</th>"
            f"<th style='padding:6px 10px;text-align:right'>Expected</th>"
            f"<th style='padding:6px 10px;text-align:right'>Worst Case</th>"
            f"<th style='padding:6px 10px;text-align:right'>Inflation Impact</th></tr>"
            f"{rows_html}</table></div>"
        )
        self(html)

    def cost_variants(
        self,
        rows: list[tuple[str, ...]],
        title: str = "Cost Impact Overview",
    ) -> None:
        """Display cost variant comparison table for the feature overview section.

        Shows two year-1 net-value views per feature:
        - Variant 1 (cash-flow): expected BV − full dev cost − year-1 opex
        - Variant 2 (P&L):       expected BV − annual installment − year-1 opex

        Parameters
        ----------
        rows:
            Output of ``BlockchainCaseStudyService.cost_variant_rows()``.
            Each row: (name, expected_bv, dev_cost, opex, v1_net, installment, v2_net)
        title:
            Card title.
        """
        from ..styling import COLORS

        hdr_bg = COLORS.primary
        hdr_fg = COLORS.background
        alt_bg = COLORS.surface

        # noinspection PyShadowingNames
        def _cell_color(val: str) -> str:
            return COLORS.success if val.startswith("+") else COLORS.danger

        rows_html = ""
        for i, row in enumerate(rows):
            name, exp, dev, opex, v1, dep, v2 = row
            bg = alt_bg if i % 2 == 0 else COLORS.background
            short = name.split(": ", 1)[-1] if ": " in name else name
            rows_html += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:6px 10px;font-weight:600'>{short}</td>"
                f"<td style='padding:6px 10px;text-align:right'>{exp}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>{dev}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>{opex}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
                f"color:{_cell_color(v1)}'>{v1}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>{dep}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
                f"color:{_cell_color(v2)}'>{v2}</td>"
                f"</tr>"
            )

        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {hdr_bg};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
            f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
            f"text-align:left;font-weight:700;font-size:14px'>📊 {title}</caption>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
            f"<th style='padding:6px 10px;text-align:left' rowspan='2'>Feature</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>Expected BV</th>"
            f"<th style='padding:6px 10px;text-align:center;border-bottom:1px solid {hdr_fg}' colspan='3'>"
            f"Option A — Upfront Payment</th>"
            f"<th style='padding:6px 10px;text-align:center;border-bottom:1px solid {hdr_fg}' colspan='2'>"
            f"Option B — Installment</th></tr>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg};font-size:11px'>"
            f"<th style='padding:4px 10px;text-align:right'>Dev Cost</th>"
            f"<th style='padding:4px 10px;text-align:right'>OpEx/yr</th>"
            f"<th style='padding:4px 10px;text-align:right'>Net Year 1</th>"
            f"<th style='padding:4px 10px;text-align:right'>Installment</th>"
            f"<th style='padding:4px 10px;text-align:right'>Net Year 1</th></tr>"
            f"{rows_html}</table>"
            f"<div style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
            f"Option A: BV − Dev Cost − OpEx &nbsp;|&nbsp; "
            f"Option B: BV − Annual Installment − OpEx"
            f"</div></div>"
        )
        self(html)

    def year1_overview(
        self,
        rows: list[tuple],
        title: str = "Year 1 Overview — Business Value vs. Costs",
    ) -> None:
        """Comprehensive Year-1 overview table per feature + portfolio total.

        Each row tuple (from BlockchainCaseStudyService.year1_overview_rows()):
            (name, expected, var_95, cvar_95,
             dev_cost, opex, v1_net,
             installment, v2_net, is_total)
        """
        from ..styling import COLORS

        hdr_bg = COLORS.background
        hdr_fg = COLORS.neutral

        rows_html = ""
        for i, row in enumerate(rows):
            name, exp, var95, cvar95, dev, opex, v1, depr, v2, is_total = row
            bg = _y1_row_background(i, is_total, COLORS)
            style = "font-weight:700;" if is_total else ""
            row_class = "fhs-y1-total" if is_total else ""
            value_html = (
                _y1_stack_html("Expected", _y1_amount_html(exp))
                + _y1_stack_html(
                    "Floor", _y1_amount_html(var95, COLORS.danger), COLORS.danger
                )
                + _y1_stack_html(
                    "Tail", _y1_amount_html(cvar95, COLORS.danger), COLORS.danger
                )
            )
            option_a_html = (
                _y1_stack_html("Investment", _y1_amount_html(dev, COLORS.neutral))
                + _y1_stack_html("OpEx / year", _y1_amount_html(opex, COLORS.neutral))
                + _y1_stack_html("Net Year 1", _y1_net_html(v1, COLORS))
            )
            option_b_html = (
                _y1_stack_html("Installment", _y1_amount_html(depr, COLORS.neutral))
                + _y1_stack_html("OpEx / year", _y1_amount_html(opex, COLORS.neutral))
                + _y1_stack_html("Net Year 1", _y1_net_html(v2, COLORS))
            )
            rows_html += (
                f"<tr class='{row_class}' style='background:{bg};{style}'>"
                f"<td class='fhs-y1-feature' style='background:{bg};'>{name}</td>"
                f"<td class='fhs-y1-cell'>{value_html}</td>"
                f"<td class='fhs-y1-cell'>{option_a_html}</td>"
                f"<td class='fhs-y1-cell'>{option_b_html}</td>"
                f"<td class='fhs-y1-decision'>{_y1_relief_html(v1, v2, COLORS)}</td>"
                f"</tr>"
            )

        html = (
            "<style>"
            ".fhs-y1-wrap{font-family:Inter,Roboto,Arial,sans-serif;"
            f"border:1px solid {COLORS.border};border-radius:8px;overflow:auto;"
            "margin:8px 0;max-width:100%;box-shadow:0 1px 3px rgba(60,64,67,.12)}"
            ".fhs-y1-title{display:flex;align-items:center;gap:10px;"
            f"padding:14px 16px;background:{COLORS.background};"
            f"border-bottom:1px solid {COLORS.border};color:{hdr_fg};font-weight:800;"
            "font-size:15px;letter-spacing:0}.fhs-y1-mark{width:8px;height:28px;"
            f"background:{COLORS.primary};display:inline-block}}.fhs-y1-table{{width:100%;"
            "min-width:940px;border-collapse:separate;border-spacing:0;font-size:13px;"
            "font-variant-numeric:tabular-nums}.fhs-y1-table th{position:sticky;"
            f"top:0;background:{hdr_bg};color:{hdr_fg};z-index:2;text-align:left;"
            f"padding:10px 14px;border-bottom:1px solid {COLORS.border};"
            "font-size:11px;text-transform:uppercase;letter-spacing:.04em}"
            ".fhs-y1-table td{padding:12px 14px;vertical-align:middle;"
            f"border-bottom:1px solid {COLORS.grid};}}.fhs-y1-feature{{position:sticky;"
            "left:0;z-index:1;min-width:180px;font-weight:800;color:"
            f"{COLORS.neutral};}}.fhs-y1-cell{{min-width:190px}}"
            ".fhs-y1-stack-row{display:flex;justify-content:space-between;gap:20px;"
            "align-items:baseline;line-height:1.65}.fhs-y1-stack-label{color:"
            f"{COLORS.subtle};font-size:11px}}.fhs-y1-stack-value{{font-weight:720;"
            "white-space:nowrap}.fhs-y1-amount,.fhs-y1-net{font-weight:760;"
            "white-space:nowrap}.fhs-y1-decision{min-width:170px}.fhs-y1-signal{"
            "display:inline-flex;flex-direction:column;gap:2px;border-left:4px solid;"
            f"background:{COLORS.background};padding:8px 10px;border-radius:6px;"
            f"box-shadow:inset 0 0 0 1px {COLORS.border};}}.fhs-y1-signal-main{{"
            "font-size:16px;font-weight:850;line-height:1}.fhs-y1-signal-label{"
            f"color:{COLORS.subtle};font-size:11px;font-weight:650;white-space:nowrap}}"
            ".fhs-y1-total td{border-top:2px solid "
            f"{COLORS.success_border};border-bottom:0}}.fhs-y1-note{{padding:9px 16px;"
            f"font-size:11px;color:{COLORS.subtle};background:{COLORS.surface}}}"
            "</style>"
            "<div class='fhs-y1-wrap'>"
            f"<div class='fhs-y1-title'><span class='fhs-y1-mark'></span><span>{title}</span></div>"
            "<table class='fhs-y1-table'>"
            "<tr>"
            "<th>Feature</th>"
            "<th>Business value</th>"
            "<th>Option A: upfront</th>"
            "<th>Option B: installment</th>"
            "<th>Year-1 signal</th>"
            "</tr>"
            f"{rows_html}</table>"
            f"<div class='fhs-y1-note'>"
            f"Option A: Expected BV − Full Investment − OpEx &nbsp;|&nbsp; "
            f"Option B: Expected BV − Annual Installment − OpEx &nbsp;|&nbsp; "
            f"Portfolio VaR/CVaR from combined Monte Carlo (not simple sum)"
            f"</div></div>"
        )
        self(html)

    def portfolio_pl_variants(
        self,
        result: PortfolioPLVariants,
        title: str = "Portfolio Year-1 P&L — Full Investment vs. Installment",
    ) -> None:
        """Display the portfolio P&L variant table with values only.

        Shows 4 BV statistics (Best/Mean/Floor/Tail) × 2 cost variants
        (V1 cash-flow, V2 P&L/accounting) plus a compact value summary.

        Parameters
        ----------
        result:
            Output of ``BlockchainCaseStudyService.portfolio_pl_variants()``.
        title:
            Card title.
        """
        from ..styling import COLORS

        hdr_bg = COLORS.primary
        hdr_fg = COLORS.background
        alt_bg = COLORS.surface

        rows_html = ""
        for i, row in enumerate(result.rows):
            bg = alt_bg if i % 2 == 0 else COLORS.background
            bv_str = f"€{row.bv:,.0f}"
            v1_str = _fmt_signed(row.v1_net)
            v2_str = _fmt_signed(row.v2_net)
            rows_html += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:6px 10px;font-weight:600'>{row.label}</td>"
                f"<td style='padding:6px 10px;text-align:right'>{bv_str}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
                f"color:{_cell_color(row.v1_net)}'>{v1_str}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-weight:700;"
                f"color:{_cell_color(row.v2_net)}'>{v2_str}</td>"
                f"</tr>"
            )

        legend = (
            f"Option A deducts: €{result.total_investment:,.0f} investment "
            f"+ €{result.total_annual_opex:,.0f} opex &nbsp;|&nbsp; "
            f"Option B deducts: €{result.total_annual_installment:,.0f} installment "
            f"+ €{result.total_annual_opex:,.0f} opex"
        )
        mean_row = next(row for row in result.rows if row.label == "Mean (Expected)")
        floor_row = next(row for row in result.rows if row.label == "Floor (BVF 95%)")
        value_summary = (
            f"Mean net: Option A {_fmt_signed(mean_row.v1_net)} &nbsp;|&nbsp; "
            f"Option B {_fmt_signed(mean_row.v2_net)} &nbsp;|&nbsp; "
            f"Floor net: Option A {_fmt_signed(floor_row.v1_net)} &nbsp;|&nbsp; "
            f"Option B {_fmt_signed(floor_row.v2_net)}"
        )

        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {hdr_bg};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
            f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
            f"text-align:left;font-weight:700;font-size:14px'>📊 {title}</caption>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
            f"<th style='padding:6px 10px;text-align:left'>Scenario</th>"
            f"<th style='padding:6px 10px;text-align:right'>Business Value</th>"
            f"<th style='padding:6px 10px;text-align:right'>"
            f"Option A Net (Upfront)</th>"
            f"<th style='padding:6px 10px;text-align:right'>"
            f"Option B Net (Installment)</th>"
            f"</tr>"
            f"{rows_html}</table>"
            f"<div style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
            f"{legend}</div>"
            f"<div style='padding:10px;font-size:13px;color:{COLORS.neutral};"
            f"border-top:1px solid {COLORS.border};background:{alt_bg}'>"
            f"{value_summary}</div>"
            f"</div>"
        )
        self(html)

    # noinspection PyUnusedLocal
    def npv_dual_table(
        self,
        rows: list[tuple],
        title: str = "NPV Analysis — Upfront vs. Installment Financing",
        discount_rate: float = 0.0,
    ) -> None:
        """Display NPV comparison table for Option A (upfront) and Option B (installment).

        Each row from ``BlockchainCaseStudyService.npv_dual_rows()``:
            (name, dev_cost, installment, installment_years,
             npv_a_exp, npv_a_floor, npv_a_ceil,
             npv_b_exp, npv_b_floor, npv_b_ceil, npv_diff_exp)
        """
        from ..styling import COLORS

        hdr_bg = COLORS.primary
        hdr_fg = COLORS.background
        alt_bg = COLORS.surface

        # noinspection PyShadowingNames
        def _eur(v: float) -> str:
            sign = "+" if v >= 0 else "−"
            col = COLORS.success if v >= 0 else COLORS.danger
            return (
                f"<span style='font-weight:700;color:{col}'>{sign}€{abs(v):,.0f}</span>"
            )

        def _diff(v: float) -> str:
            sign = "+" if v >= 0 else "−"
            col = COLORS.success if v >= 0 else COLORS.neutral
            return f"<span style='color:{col}'>{sign}€{abs(v):,.0f}</span>"

        # noinspection PyShadowingNames
        def _npv_row_html(row: tuple, bg: str) -> str:
            (
                name,
                dev_cost,
                installment,
                inst_years,
                a_exp,
                a_floor,
                _a_ceil,
                b_exp,
                b_floor,
                _b_ceil,
                diff_exp,
            ) = row
            return (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:6px 10px;font-weight:600'>{name}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>"
                f"€{dev_cost:,.0f}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>"
                f"€{installment:,.0f}×{inst_years}yr</td>"
                f"<td style='padding:6px 10px;text-align:right'>{_eur(a_exp)}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-size:11px'>{_eur(a_floor)}</td>"
                f"<td style='padding:6px 10px;text-align:right'>{_eur(b_exp)}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-size:11px'>{_eur(b_floor)}</td>"
                f"<td style='padding:6px 10px;text-align:right'>{_diff(diff_exp)}</td>"
                f"</tr>"
            )

        rows_html = ""
        for i, row in enumerate(rows):
            bg = alt_bg if i % 2 == 0 else COLORS.background
            rows_html += _npv_row_html(row, bg)

        rate_note = f" (discount rate: {discount_rate:.0%})" if discount_rate else ""
        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {hdr_bg};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
            f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
            f"text-align:left;font-weight:700;font-size:14px'>📊 {title}{rate_note}</caption>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
            f"<th style='padding:6px 10px;text-align:left' rowspan='2'>Feature</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>Dev Cost</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>Installment</th>"
            f"<th style='padding:6px 10px;text-align:center;"
            f"border-bottom:1px solid {hdr_fg}' colspan='2'>Option A — Upfront</th>"
            f"<th style='padding:6px 10px;text-align:center;"
            f"border-bottom:1px solid {hdr_fg}' colspan='2'>Option B — Installment</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>B − A</th>"
            f"</tr>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg};font-size:11px'>"
            f"<th style='padding:4px 10px;text-align:right'>Expected</th>"
            f"<th style='padding:4px 10px;text-align:right'>Floor</th>"
            f"<th style='padding:4px 10px;text-align:right'>Expected</th>"
            f"<th style='padding:4px 10px;text-align:right'>Floor</th>"
            f"</tr>"
            f"{rows_html}</table>"
            f"<div style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
            f"Option A: −Investment + Σ (BV − OpEx)/(1+r)^t &nbsp;|&nbsp; "
            f"Option B: Σ (BV − Inst − OpEx)/(1+r)^t (yrs 1..n) + Σ (BV − OpEx)/(1+r)^t (yrs n+1..T)"
            f"</div></div>"
        )
        self(html)

    # noinspection PyUnusedLocal
    def irr_dual_table(
        self,
        rows: list[tuple],
        title: str = "IRR Analysis — Upfront vs. Installment Financing",
        discount_rate: float = 0.0,
    ) -> None:
        """Display IRR comparison table for Option A (upfront) and Option B (installment).

        Each row from ``BlockchainCaseStudyService.irr_dual_rows()``:
            (name, dev_cost, installment, installment_years,
             irr_a_exp, irr_a_floor, irr_a_ceil,
             irr_b_exp, irr_b_floor, irr_b_ceil)
        """

        from ..styling import COLORS

        hdr_bg = COLORS.primary
        hdr_fg = COLORS.background
        alt_bg = COLORS.surface

        # noinspection PyShadowingNames
        def _irr(v: float, hurdle: float) -> str:
            if math.isnan(v):
                return (
                    f"<span style='color:{COLORS.success};font-size:11px'>"
                    f"Positive Y1</span>"
                )
            col = COLORS.success if v >= hurdle else COLORS.danger
            return f"<span style='font-weight:700;color:{col}'>{v:.0%}</span>"

        # noinspection PyShadowingNames
        def _irr_row_html(row: tuple, bg: str, hurdle: float) -> str:
            (
                name,
                dev_cost,
                installment,
                inst_years,
                a_exp,
                a_floor,
                _a_ceil,
                b_exp,
                b_floor,
                _b_ceil,
            ) = row
            return (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:6px 10px;font-weight:600'>{name}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>"
                f"€{dev_cost:,.0f}</td>"
                f"<td style='padding:6px 10px;text-align:right;color:{COLORS.neutral}'>"
                f"€{installment:,.0f}×{inst_years}yr</td>"
                f"<td style='padding:6px 10px;text-align:right'>{_irr(a_exp, hurdle)}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-size:11px'>"
                f"{_irr(a_floor, hurdle)}</td>"
                f"<td style='padding:6px 10px;text-align:right'>{_irr(b_exp, hurdle)}</td>"
                f"<td style='padding:6px 10px;text-align:right;font-size:11px'>"
                f"{_irr(b_floor, hurdle)}</td>"
                f"</tr>"
            )

        hurdle = discount_rate
        rows_html = ""
        for i, row in enumerate(rows):
            bg = alt_bg if i % 2 == 0 else COLORS.background
            rows_html += _irr_row_html(row, bg, hurdle)

        hurdle_note = f" vs hurdle {discount_rate:.0%}" if discount_rate else ""
        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {hdr_bg};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse;font-size:13px'>"
            f"<caption style='background:{hdr_bg};color:{hdr_fg};padding:8px 10px;"
            f"text-align:left;font-weight:700;font-size:14px'>"
            f"📊 {title}{hurdle_note}</caption>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg}'>"
            f"<th style='padding:6px 10px;text-align:left' rowspan='2'>Feature</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>Dev Cost</th>"
            f"<th style='padding:6px 10px;text-align:right' rowspan='2'>Installment</th>"
            f"<th style='padding:6px 10px;text-align:center;"
            f"border-bottom:1px solid {hdr_fg}' colspan='2'>Option A — Upfront</th>"
            f"<th style='padding:6px 10px;text-align:center;"
            f"border-bottom:1px solid {hdr_fg}' colspan='2'>Option B — Installment</th>"
            f"</tr>"
            f"<tr style='background:{hdr_bg};color:{hdr_fg};font-size:11px'>"
            f"<th style='padding:4px 10px;text-align:right'>Expected</th>"
            f"<th style='padding:4px 10px;text-align:right'>Floor</th>"
            f"<th style='padding:4px 10px;text-align:right'>Expected</th>"
            f"<th style='padding:4px 10px;text-align:right'>Floor</th>"
            f"</tr>"
            f"{rows_html}</table>"
            f"<div style='padding:6px 10px;font-size:11px;color:{COLORS.neutral}'>"
            f"'Positive Y1' = all net cashflows positive in year 1 — no finite IRR "
            f"(favourable: installments are already covered). "
            f"Colors: green = above hurdle rate, red = below."
            f"</div></div>"
        )
        self(html)

    # noinspection PyUnusedLocal
    def feature_cashflow_comparison(
        self,
        sched_a: dict,
        sched_b: dict,
        *,
        title: str = "3-Year Net Cash Flow — All Features",
        discount_rate: float = 0.0,
        irr_rows: list | None = None,
        portfolio_irr_a: float | None = None,
        portfolio_irr_b: float | None = None,
    ) -> None:
        """Display two stacked cashflow tables — one per financing option.

        Each table has one row per feature plus a Portfolio Total row.
        Columns: Year 0 | Year 1 | Year 2 | Year 3 | NPV [| IRR].

        When ``irr_rows`` is supplied (output of
        ``BlockchainCaseStudyService.irr_dual_rows()``), an IRR column is
        appended to each table so the reader sees the cashflows that produced
        each yield side by side.

        Parameters
        ----------
        sched_a : dict
            Option A (upfront) schedule.
        sched_b : dict
            Option B (installment) schedule.
        title : str
            Section header above both tables.
        discount_rate : float
            Shown in footer note and used to colour IRR values relative to
            the hurdle rate.
        irr_rows : list | None
            Per-feature IRR data from ``irr_dual_rows()``. Each tuple:
            ``(name, dev_cost, installment, inst_years,
            a_exp, a_floor, a_ceil, b_exp, b_floor, b_ceil)``.
        portfolio_irr_a : float | None
            Portfolio-level IRR for Option A. Shown in portfolio total row.
        portfolio_irr_b : float | None
            Portfolio-level IRR for Option B.
        """

        from ..styling import COLORS

        accent_a = COLORS.primary
        accent_b = COLORS.success
        hurdle = discount_rate

        # Build per-feature IRR lookup: name → (irr_a, irr_b)
        irr_map_a: dict[str, float] = {}
        irr_map_b: dict[str, float] = {}
        if irr_rows:
            for row in irr_rows:
                irr_map_a[row[0]] = row[4]  # a_exp
                irr_map_b[row[0]] = row[7]  # b_exp

        feat_names = [r["name"] for r in sched_a["rows"]]
        pf_name = sched_a["portfolio"]["name"]

        irr_panel = _irr_comparison_panel(
            irr_rows,
            irr_map_a,
            irr_map_b,
            hurdle,
            portfolio_irr_a,
            portfolio_irr_b,
            feat_names,
            pf_name,
        )
        html_a = _render_cashflow_table(sched_a, accent_a, hurdle)
        html_b = _render_cashflow_table(sched_b, accent_b, hurdle)

        # Benefit callout
        benefit = sched_b["portfolio"]["npv"] - sched_a["portfolio"]["npv"]
        bc = COLORS.success if benefit >= 0 else COLORS.danger
        bs = "+" if benefit >= 0 else "−"
        rate_note = f" at {discount_rate:.0%} discount rate" if discount_rate else ""
        callout = (
            f"<div style='border:2px solid {bc};border-radius:10px;"
            f"padding:12px 20px;margin:12px 0;"
            f"display:flex;flex-wrap:wrap;align-items:center;gap:20px'>"
            f"<div style='font-size:26px;font-weight:900;color:{bc};"
            f"white-space:nowrap'>{bs}€{abs(benefit):,.0f}</div>"
            f"<div style='font-size:13px'>"
            f"<span style='font-weight:700;color:{bc}'>"
            f"Portfolio NPV advantage of Option B over Option A{rate_note}.</span>"
            f"<span style='color:{COLORS.neutral}'> "
            f"Deferring investment into annual installments reduces the present value "
            f"of costs — later payments are worth less in today's terms.</span>"
            f"</div></div>"
        )

        wrapper = (
            f"<div style='margin:8px 0'>"
            f"<div style='font-size:17px;font-weight:700;padding:6px 0 10px;"
            f"color:{COLORS.neutral};border-bottom:2px solid {COLORS.border};"
            f"margin-bottom:12px'>{title}</div>"
            f"{irr_panel}{html_a}{html_b}{callout}</div>"
        )
        self(wrapper)

    def financing_recommendation(
        self,
        recommendation_text: str,
        *,
        title: str = "Financing Decision — Option A vs. Option B",
    ) -> None:
        """Display a plain-English financing recommendation box."""
        from ..styling import COLORS

        html = (
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {COLORS.secondary};margin:8px 0'>"
            f"<div style='background:{COLORS.secondary};color:{COLORS.background};"
            f"padding:8px 10px;font-weight:700;font-size:14px'>💡 {title}</div>"
            f"<div style='padding:12px 14px;font-size:13px;line-height:1.6;"
            f"color:{COLORS.neutral}'>{recommendation_text}</div>"
            f"</div>"
        )
        self(html)

    # noinspection PyUnusedLocal
    def capital_budgeting_summary(
        self,
        npv_a,
        npv_b,
        irr_a,
        irr_b,
        pi_a: float,
        pi_b: float,
        discount_rate: float,
        *,
        title: str = "Portfolio Capital Budgeting Summary",
        verdict_message: str = "",
        verdict_is_go: bool = True,
    ) -> None:
        """Compact two-column A vs. B comparison table (NPV, IRR, PI, benefit).

        Replaces the verbose ``show.metrics()`` list with a clean side-by-side
        table so POs and FRMs can compare both options at a glance.

        Parameters
        ----------
        npv_a, npv_b:
            NpvSummary objects for Option A (upfront) and Option B (installment).
        irr_a, irr_b:
            IrrSummary objects for both options.
        pi_a, pi_b:
            Profitability Index: NPV / PV(investment). Always finite and
            comparable across options.
        discount_rate:
            Hurdle rate — shown in IRR comparison context.
        title:
            Section title.
        verdict_message:
            Optional GO/CAUTION verdict line shown below the table.
        verdict_is_go:
            If True the verdict box is green; orange otherwise.
        """

        from ..template_engine import render

        benefit = npv_b.expected - npv_a.expected
        benefit_floor = npv_b.var_95 - npv_a.var_95
        self(
            render(
                "capital_budgeting/summary.html.j2",
                title=title,
                npv_a_expected=npv_a.expected,
                npv_a_var95=npv_a.var_95,
                npv_b_expected=npv_b.expected,
                npv_b_var95=npv_b.var_95,
                irr_a_expected=irr_a.expected,
                irr_b_expected=irr_b.expected,
                pi_a=pi_a,
                pi_b=pi_b,
                discount_rate=discount_rate,
                benefit=benefit,
                benefit_floor=benefit_floor,
                verdict_message=verdict_message,
                verdict_is_go=verdict_is_go,
            )
        )

    @staticmethod
    def cashflow_chart(
        sched_a: dict,
        sched_b: dict,
        *,
        title: str = "Net Cash Flow per Year — Option A vs. Option B",
    ) -> None:
        """Grouped bar chart: portfolio net cashflows year by year (A vs B).

        Delegates to ``charts.capital_budgeting.plot_cashflow_bars``.
        The chart is the clearest way to show that Option A has a large
        Year-0 outflow while Option B spreads costs into the business-value years.
        """
        from ..charts.capital_budgeting import plot_cashflow_bars

        plot_cashflow_bars(sched_a, sched_b, title=title)

    # noinspection PyUnusedLocal
    def npv_comparison_chart(
        self,
        npv_a,
        npv_b,
        pi_a: float,
        pi_b: float,
        discount_rate: float = 0.0,
        *,
        title: str = "Portfolio NPV — Option A vs. Option B",
    ) -> None:
        """NPV bar chart followed by a structured HTML risk summary table.

        The chart shows Expected NPV bars with PI inside and the Δ advantage
        callout. The HTML table below answers the three C-level questions:

        - Which option creates more value? (Expected NPV)
        - What is the worst-case exposure? (BVF 95% floor)
        - What is the upside potential? (P95)
        - How efficient is the capital? (PI)

        Delegates chart to ``charts.capital_budgeting.plot_npv_comparison``.
        """

        from ..charts.capital_budgeting import plot_npv_comparison
        from ..styling import COLORS

        plot_npv_comparison(
            npv_a_expected=npv_a.expected,
            npv_a_floor=npv_a.var_95,
            npv_a_ceiling=npv_a.p95,
            npv_b_expected=npv_b.expected,
            npv_b_floor=npv_b.var_95,
            npv_b_ceiling=npv_b.p95,
            pi_a=pi_a,
            pi_b=pi_b,
            discount_rate=discount_rate,
            title=title,
        )

        # ── HTML risk summary table ────────────────────────────────────────
        benefit = npv_b.expected - npv_a.expected
        bc = COLORS.success if benefit >= 0 else COLORS.danger
        bs = "+" if benefit >= 0 else "−"
        decision_label = (
            "Option B creates more value"
            if benefit >= 0
            else "Option A creates more value"
        )

        summary_html = (
            f"<div style='display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 10px'>"
            f"{_npv_summary_card('Option A expected NPV', f'€{npv_a.expected:,.0f}', COLORS.primary, COLORS.surface, COLORS)}"
            f"{_npv_summary_card('Option B expected NPV', f'€{npv_b.expected:,.0f}', COLORS.secondary, COLORS.surface, COLORS)}"
            f"{_npv_summary_card(decision_label, f'{bs}€{abs(benefit):,.0f}', bc, _npv_benefit_background(benefit, COLORS), COLORS)}"
            f"</div>"
        )

        rows_data = [
            (
                "▲ P95 — best 5% of simulations",
                format_value_k(npv_a.p95),
                format_value_k(npv_b.p95),
                False,
            ),
            (
                "Expected NPV",
                format_value_k(npv_a.expected),
                format_value_k(npv_b.expected),
                True,
            ),
            (
                "▼ BVF 95% — worst 5% of simulations",
                format_value_k(npv_a.var_95),
                format_value_k(npv_b.var_95),
                False,
            ),
            ("PI — NPV ÷ PV(investment)", f"{pi_a:.2f}×", f"{pi_b:.2f}×", False),
        ]

        rows_html = ""
        for i, (label, val_a, val_b, bold) in enumerate(rows_data):
            bg = COLORS.surface if i % 2 == 0 else COLORS.background
            fw = "700" if bold else "400"
            fs = "14px" if bold else "13px"
            rows_html += (
                f"<tr style='background:{bg}'>"
                f"<td style='padding:8px 14px;color:{COLORS.neutral};font-size:{fs}"
                f";font-weight:{fw}'>{label}</td>"
                f"<td style='padding:8px 14px;text-align:right;font-size:{fs}"
                f";font-weight:{fw};color:{COLORS.primary}'>{val_a}</td>"
                f"<td style='padding:8px 14px;text-align:right;font-size:{fs}"
                f";font-weight:{fw};color:{COLORS.secondary}'>{val_b}</td>"
                f"</tr>"
            )

        rate_note = f" · discount rate {discount_rate:.0%}" if discount_rate else ""
        html = (
            f"{summary_html}"
            f"<div style='border:1px solid {COLORS.border};border-radius:8px;"
            f"overflow:auto;border-left:4px solid {bc};margin:8px 0'>"
            f"<table style='width:100%;border-collapse:collapse'>"
            f"<tr style='background:{COLORS.surface}'>"
            f"<th style='padding:7px 14px;text-align:left;font-size:12px;"
            f"color:{COLORS.neutral}'>Monte Carlo simulation results{rate_note}</th>"
            f"<th style='padding:7px 14px;text-align:right;font-size:12px;"
            f"color:{COLORS.primary}'>Option A — Upfront</th>"
            f"<th style='padding:7px 14px;text-align:right;font-size:12px;"
            f"color:{COLORS.secondary}'>Option B — Installment</th>"
            f"</tr>"
            f"{rows_html}"
            f"<tr style='background:{COLORS.surface};border-top:2px solid {bc}'>"
            f"<td style='padding:9px 14px;font-weight:700;color:{COLORS.neutral}"
            f";font-size:13px'>Option B advantage (Δ Expected NPV)</td>"
            f"<td colspan='2' style='padding:9px 14px;text-align:right;"
            f"font-weight:800;font-size:15px;color:{bc}'>"
            f"{bs}€{abs(benefit) / 1_000:,.0f}k</td>"
            f"</tr>"
            f"</table></div>"
        )
        self(html)

    @staticmethod
    def irr_chart(
        rows: list,
        portfolio_irr_a: float,
        portfolio_irr_b: float,
        hurdle_rate: float = 0.08,
        *,
        title: str = "IRR per Feature — Option A vs. Option B",
    ) -> None:
        """Horizontal lollipop IRR chart: per-feature + portfolio aggregate.

        Delegates to ``charts.capital_budgeting.plot_irr_feature_chart``.

        Parameters
        ----------
        rows:
            Output of ``BlockchainCaseStudyService.irr_dual_rows()``.
        portfolio_irr_a:
            Portfolio-level IRR under upfront financing (expected value).
        portfolio_irr_b:
            Portfolio-level IRR under installment financing (expected value).
        hurdle_rate:
            Minimum required return — shown as a vertical reference line.
        title:
            Chart title.
        """
        from ..charts.capital_budgeting import plot_irr_feature_chart

        plot_irr_feature_chart(
            rows=rows,
            portfolio_irr_a=portfolio_irr_a,
            portfolio_irr_b=portfolio_irr_b,
            hurdle_rate=hurdle_rate,
            title=title,
        )

    @staticmethod
    def npv_rate_curve(
        sched_a: dict,
        sched_b: dict,
        hurdle_rate: float = 0.08,
        irr_a: float | None = None,
        irr_b: float | None = None,
        *,
        title: str = "NPV vs. Discount Rate — Option A vs. Option B",
    ) -> None:
        """NPV-vs-discount-rate curve for Option A and Option B.

        Option A (blue) crosses zero at IRR_A. Option B (green) crosses zero
        at IRR_B, which is higher because the Year-0 installment is smaller
        than the full upfront investment.

        Delegates to ``charts.capital_budgeting.plot_npv_rate_curve``.

        Parameters
        ----------
        sched_a:
            Option A cashflow schedule from ``feature_cashflow_schedules()``.
            Uses the ``portfolio.cashflows`` list.
        sched_b:
            Option B schedule (same structure).
        hurdle_rate:
            Minimum required return — shown as a dashed vertical line.
        irr_a:
            Pre-computed IRR_A (optional). Derived from cashflows if None.
        irr_b:
            Pre-computed IRR_B (optional). Annotated when within display range.
        title:
            Chart title.
        """
        from ..charts.capital_budgeting import plot_npv_rate_curve

        plot_npv_rate_curve(
            cashflows_a=sched_a["portfolio"]["cashflows"],
            cashflows_b=sched_b["portfolio"]["cashflows"],
            hurdle_rate=hurdle_rate,
            irr_a=irr_a,
            irr_b=irr_b,
            title=title,
        )

    def year1_business_value_snapshot(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Year 1 Business Value Snapshot",
    ) -> None:
        """Render the standard year-1 expected-vs-floor business-value snapshot table."""
        self.sensitivity(
            rows,
            ("Feature", "Expected Business Value (Year 1)", "BVF 95% Floor"),
            title=title,
        )

    def roi_analysis_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "ROI Analysis - Return per EUR invested",
    ) -> None:
        """Render the ROI analysis table including OpEx and net ROI columns."""
        self.sensitivity(
            rows,
            (
                "Feature",
                "Investment",
                "Annual OpEx",
                "Expected Business Value (Year 1)",
                "ROI (Gross)",
                "Net ROI (−OpEx)",
            ),
            title=title,
        )

    def growth_inputs_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Growth Inputs from Scenario Config",
    ) -> None:
        """Render configured annual growth assumptions per feature."""
        self.sensitivity(
            rows,
            ("Feature", "Annual Growth Assumption"),
            title=title,
        )

    def npv_analysis_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str,
    ) -> None:
        """Render the NPV analysis table with expected/floor/ceiling columns."""
        self.sensitivity(
            rows,
            ("Feature", "Investment", "NPV (Expected)", "NPV (Floor)", "NPV (Ceiling)"),
            title=title,
        )

    def irr_analysis_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str,
    ) -> None:
        """Render the IRR analysis table with expected/floor/ceiling columns."""
        self.sensitivity(
            rows,
            ("Feature", "Investment", "IRR (Expected)", "IRR (Floor)", "IRR (Ceiling)"),
            title=title,
        )

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

"""Risk display methods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fhs.application.risk_layers_operations import FeatureRiskLayerTables
    from fhs.core.model.config.scenario import ScenarioRiskModel
    from fhs.core.model.value_objects.risk_layer_stats import (
        PortfolioRiskLayers,
        RiskLayerStats,
    )

from ..styling import COLORS
from .cards import (
    downside_risk_card,
)
from .tables import (
    sensitivity_table,
)

EXPECTED_PORTFOLIO_BUSINESS_VALUE_LABEL = "Expected Portfolio Business Value"
RISK_LAYER_LABEL = "Risk Layer"
EXPECTED_BUSINESS_VALUE_LABEL = "Expected Business Value"


class _RiskMixin:
    # Host stubs for static typing; concrete behavior comes from _PrimitivesMixin.
    # noinspection PyUnusedLocal
    def __call__(self, html: str) -> None:  # pragma: no cover - typing stub
        del html

    # noinspection PyUnusedLocal
    def sensitivity_html(
        self,
        _rows: list[tuple[Any, ...]],
        _headers: tuple[str, ...],
        **_kwargs: Any,
    ) -> str:  # pragma: no cover - typing stub
        return ""

    # noinspection PyUnusedLocal
    @staticmethod
    def columns(
        *html_blocks: str,
        gap: str = "16px",
        min_width: str = "250px",
    ) -> None:  # pragma: no cover - typing stub
        del html_blocks, gap, min_width

    # noinspection PyUnusedLocal
    @staticmethod
    def metrics(
        rows: list[tuple[str, str, str | None]],
        *,
        title: str = "Metrics",
        metric_header: str = "Metric",
        value_header: str = "Value",
    ) -> None:  # pragma: no cover - typing stub
        del rows, title, metric_header, value_header

    def downside_risk(self, result, *, title: str = "Downside Risk Summary") -> None:
        self(
            downside_risk_card(
                result.var_95,
                result.cvar_95,
                result.expected_value,
                title=title,
            )
        )

    def sensitivity(
        self,
        rows: list[tuple[Any, ...]],
        headers: tuple[str, ...],
        **kwargs: Any,
    ) -> None:
        self(sensitivity_table(rows, headers, **kwargs))

    def feature_risk_layers(
        self,
        risk_tables: FeatureRiskLayerTables,
        *,
        expected_title: str = "Expected Business Value at Each Risk Layer (per feature)",
        probability_title: str = "Risk Configuration per Feature Cluster",
        retention_title: str = "Feature Business Value Retention across All Risk Layers",
    ) -> None:
        """Render the standard three-table block for feature risk layers.

        The expected BV table is displayed first; risk configuration (wider table)
        and retention tables span full width below for optimal readability.
        """
        self.sensitivity(
            rows=list(risk_tables.expected_rows),
            headers=tuple(risk_tables.expected_headers),
            title=expected_title,
        )
        self.sensitivity(
            rows=list(risk_tables.probability_rows),
            headers=tuple(risk_tables.prob_headers),
            title=probability_title,
        )
        self.sensitivity(
            rows=list(risk_tables.retention_rows),
            headers=tuple(risk_tables.retention_headers),
            title=retention_title,
        )

    @staticmethod
    def feature_risk_layer_decay(
        feature_names: list[str],
        expected_matrix: list[list[float]],
        layer_labels: list[str] | None = None,
        *,
        title: str = "Feature Expected Business Value Decay Across Risk Layers",
    ) -> None:
        """Render per-feature risk-layer decay line chart."""
        from ..charts.risk import plot_feature_risk_layer_decay

        plot_feature_risk_layer_decay(
            feature_names,
            expected_matrix,
            layer_labels,
            title=title,
        )

    def risk_factor_sensitivity(
        self,
        market_rows: list[tuple[str, str]],
        global_rows: list[tuple[str, str]],
        component_rows: list[tuple[str, str]],
    ) -> None:
        """Render market/global/component sensitivity tables with standard formatting."""
        self.sensitivity(
            rows=market_rows,
            headers=("Market Probability", EXPECTED_PORTFOLIO_BUSINESS_VALUE_LABEL),
            title="Market Risk Sensitivity",
        )
        self.sensitivity(
            rows=global_rows,
            headers=("Global Probability", EXPECTED_PORTFOLIO_BUSINESS_VALUE_LABEL),
            title="Global Risk Sensitivity",
        )
        self.sensitivity(
            rows=component_rows,
            headers=(
                "Cluster",
                "Failure Probability",
                EXPECTED_PORTFOLIO_BUSINESS_VALUE_LABEL,
            ),
            title="Component Risk Sensitivity by Platform Cluster",
        )

    def budget_risk_path(
        self,
        path: list[Any],
        *,
        title: str = "Budget Path - Floor and Risk Class (ILP var_floor)",
    ) -> None:
        """Render standardized budget risk path rows with floor/safety/risk columns."""
        rows = [
            (
                row.label,
                str(row.selected_count),
                f"EUR {row.investment:,.0f}",
                f"EUR {row.l1_floor:,.0f}",
                f"EUR {row.l2_floor:,.0f}",
                f"EUR {row.l3_floor:,.0f}",
                f"EUR {row.l3_safety_buffer:,.0f}",
                row.risk_class,
            )
            for row in path
        ]
        self.sensitivity(
            rows,
            (
                "Budget Level",
                "Num Features",
                "Investment",
                "Base Case Floor",
                "Development Risk Floor",
                "Crisis Shock Floor",
                "Crisis Shock Safety Buffer",
                "Risk Class",
            ),
            title=title,
        )

    def three_level_risk_summary(
        self,
        risk_l2: dict[str, Any],
        risk_l3: dict[str, Any],
        *,
        title: str = "Three-Level Risk Summary",
    ) -> None:
        """Render base/development/crisis layer summary from risk analyzer output."""
        rows = [
            (
                "Base Case (market uncertainty)",
                f"EUR {risk_l2['market_expected']:,.0f}",
                f"EUR {risk_l2['market_var_95']:,.0f}",
                "Baseline",
            ),
            (
                "After Development Risk (delivery failure)",
                f"EUR {risk_l2['simulated_expected']:,.0f}",
                f"EUR {risk_l2['simulated_var_95']:,.0f}",
                f"Floor change vs Base Case: {risk_l2['var_delta_pct']:+.1f}%",
            ),
            (
                "After Crisis Shock (global event)",
                f"EUR {risk_l3['shocked_expected']:,.0f}",
                f"EUR {risk_l3['shocked_var_95']:,.0f}",
                f"Floor change vs Base Case: {risk_l3['shocked_var_delta_pct']:+.1f}%",
            ),
        ]
        self.sensitivity(
            rows,
            (
                RISK_LAYER_LABEL,
                EXPECTED_BUSINESS_VALUE_LABEL,
                "Business Value Floor (BVF 95%)",
                "Comment",
            ),
            title=title,
        )

    def stress_scenario_table(
        self,
        baseline: RiskLayerStats,
        scenarios: list[dict[str, Any]],
        *,
        title: str = "Stress Scenario Table",
    ) -> None:
        """Render baseline + stress scenario floor table from stress scenario output."""
        rows = [
            (
                "Baseline",
                f"EUR {baseline.expected:,.0f}",
                f"EUR {baseline.var_95:,.0f}",
                "0.0%",
            )
        ] + [
            (
                item["name"],
                f"EUR {item['expected']:,.0f}",
                f"EUR {item['var_95']:,.0f}",
                f"{item['var_delta_pct']:+.1f}%",
            )
            for item in scenarios
        ]
        self.sensitivity(
            rows,
            (
                "Scenario",
                EXPECTED_BUSINESS_VALUE_LABEL,
                "Business Value Floor (BVF 95%)",
                "Floor Change vs Baseline",
            ),
            title=title,
        )

    def llp_delivery_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Feature Delivery Risk Table (all features)",
    ) -> None:
        """Render the standard LLP delivery-risk table for feature comparison."""
        self.sensitivity(
            rows,
            (
                "Feature",
                "LLP",
                EXPECTED_BUSINESS_VALUE_LABEL,
                "At-Risk Business Value",
                "Dependency Cluster",
            ),
            title=title,
        )

    def business_value_loss_by_risk_dimension(
        self,
        delivery_loss: float,
        market_loss: float,
        component_loss: float,
        global_loss: float,
        base_expected: float,
        *,
        title: str = "Business Value Loss by Risk Dimension",
    ) -> None:
        """Render standardized business-value-loss table for delivery/market/component/global layers."""
        total_loss = delivery_loss + market_loss + component_loss + global_loss
        total_pct = (100.0 * total_loss / base_expected) if base_expected > 0 else 0.0
        rows = [
            (
                "Delivery risk",
                f"EUR {delivery_loss:,.0f}",
                f"{(100.0 * delivery_loss / base_expected) if base_expected > 0 else 0.0:.1f}%",
            ),
            (
                "Market risk",
                f"EUR {market_loss:,.0f}",
                f"{(100.0 * market_loss / base_expected) if base_expected > 0 else 0.0:.1f}%",
            ),
            (
                "Component risk",
                f"EUR {component_loss:,.0f}",
                f"{(100.0 * component_loss / base_expected) if base_expected > 0 else 0.0:.1f}%",
            ),
            (
                "Global risk",
                f"EUR {global_loss:,.0f}",
                f"{(100.0 * global_loss / base_expected) if base_expected > 0 else 0.0:.1f}%",
            ),
            (
                "Total risk loss",
                f"EUR {total_loss:,.0f}",
                f"{total_pct:.1f}%",
            ),
        ]
        self.sensitivity(
            rows,
            (
                "Risk Dimension",
                "Business Value Loss (EUR)",
                "% of Base Business Value",
            ),
            title=title,
        )

    def portfolio_risk_waterfall(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Portfolio Risk Waterfall (ILP-selected features)",
    ) -> None:
        """Render the standard portfolio risk waterfall table."""
        self.sensitivity(
            rows,
            (
                RISK_LAYER_LABEL,
                EXPECTED_BUSINESS_VALUE_LABEL,
                "Business Value Lost at This Layer",
            ),
            title=title,
        )

    def cross_factor_sensitivity_summary(
        self,
        r2_low: float,
        r2_high: float,
        r3_low: float,
        r3_high: float,
        *,
        title: str = "Cross-Factor Sensitivity - Expected Business Value Impact",
    ) -> None:
        """Render market/global low-vs-high risk impact summary table."""
        rows = [
            (
                "Market shock (10% -> 30%)",
                f"EUR {r2_low:,.0f}",
                f"EUR {r2_high:,.0f}",
                f"EUR {r2_high - r2_low:,.0f}",
            ),
            (
                "Global crisis (2.5% -> 7.5%)",
                f"EUR {r3_low:,.0f}",
                f"EUR {r3_high:,.0f}",
                f"EUR {r3_high - r3_low:,.0f}",
            ),
        ]
        self.sensitivity(
            rows,
            (
                "Risk Factor",
                "Expected Business Value (low risk)",
                "Expected Business Value (high risk)",
                "Business Value Impact (EUR)",
            ),
            title=title,
        )

    def risk_model_configuration(
        self,
        risk_model: ScenarioRiskModel,
        *,
        title: str = "Risk Model Configuration (from blockchain.yaml)",
    ) -> None:
        """Render the standard risk model overview table used in notebook setup."""
        rows = [
            (
                "Delivery risk",
                "Per feature",
                "Feature is not delivered -> sunk cost",
            ),
            (
                "Market risk",
                f"{risk_model.risk_2_market_probability:.0%} probability",
                f"Business value drops to {risk_model.risk_2_market_multiplier:.0%} of expected",
            ),
            (
                "Global risk",
                f"{risk_model.risk_3_global_probability:.0%} probability",
                f"Business value drops to {risk_model.risk_3_global_multiplier:.0%} of expected",
            ),
            (
                "Component risk",
                f"{risk_model.default_component_probability:.0%} default",
                f"Business value drops to {risk_model.component_risk_multiplier:.0%} of expected",
            ),
        ]
        self.sensitivity(
            rows,
            ("Risk Dimension", "Probability / Scope", "Impact when triggered"),
            title=title,
        )

    def risk_summary_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Risk Summary",
    ) -> None:
        """Render the standard feature expected-vs-floor risk summary table."""
        self.sensitivity(
            rows,
            ("Feature", EXPECTED_BUSINESS_VALUE_LABEL, "BVF 95% Floor"),
            title=title,
        )

    # ── New methods for Notebook 05 (05-improve.md) ──────────────────────

    def executive_risk_summary(
        self,
        before: float,
        after: float,
        investment: float,
        dominant_risk: str,
        *,
        profitability_pct: float | None = None,
        title: str = "Portfolio Risk Summary",
    ) -> None:
        """Render the executive risk summary box — the answer first.

        Shows the conclusion, the value flow before/after risk, and the
        investment comparison without numbered or table-like ranking cues.
        """
        at_risk = before - after
        at_risk_pct = 100.0 * at_risk / before if before > 0 else 0.0
        retained_pct = max(0.0, 100.0 - at_risk_pct)
        net = after - investment
        is_profitable = net > 0
        net_color = COLORS.success if is_profitable else COLORS.danger
        verdict = (
            "profitable on expected value"
            if is_profitable
            else "NOT profitable on expected value"
        )
        net_sign = "+" if net > 0 else ""

        def _metric_card(label: str, value: str, note: str, color: str) -> str:
            return (
                f'<div style="flex:1;min-width:210px;border:1px solid {COLORS.border};'
                f"border-radius:4px;padding:12px 14px;background:transparent;"
                f'color:inherit;">'
                f'<div style="font-size:12px;color:{COLORS.subtle};text-transform:uppercase;'
                f'letter-spacing:0.4px;">{label}</div>'
                f'<div style="font-size:22px;font-weight:bold;color:{color};margin-top:4px;">'
                f"{value}</div>"
                f'<div style="font-size:12px;color:{COLORS.subtle};margin-top:4px;">'
                f"{note}</div>"
                f"</div>"
            )

        headline_html = (
            f'<div style="padding:10px 14px;border-left:4px solid {net_color};'
            f'margin-bottom:14px;background:transparent;color:inherit;">'
            f'<div style="font-size:12px;color:{COLORS.subtle};text-transform:uppercase;'
            f'letter-spacing:0.4px;">Decision signal</div>'
            f'<div style="font-size:18px;font-weight:bold;color:{net_color};">'
            f"Portfolio is {verdict}</div>"
            f'<div style="font-size:13px;color:inherit;margin-top:2px;">'
            f"Expected net position after all risks: "
            f'<b style="color:{net_color};">{net_sign}EUR {net:,.0f}</b>'
            f"</div></div>"
        )

        flow_html = (
            f'<div style="display:flex;gap:12px;align-items:stretch;'
            f'flex-wrap:wrap;margin-bottom:12px;">'
            f"{_metric_card('Before risk', f'EUR {before:,.0f}', 'Expected business value before risk layers', 'inherit')} "
            f"{_metric_card('Risk impact', f'-EUR {at_risk:,.0f}', f'{at_risk_pct:.0f}% eroded, {retained_pct:.0f}% retained', COLORS.danger)} "
            f"{_metric_card('After all risks', f'EUR {after:,.0f}', 'Expected business value after full risk overlay', 'inherit')} "
            f"</div>"
        )

        investment_html = (
            f'<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;">'
            f'<div style="flex:1;min-width:210px;color:inherit;">'
            f'<span style="color:{COLORS.subtle};">Investment:</span> '
            f"<b>EUR {investment:,.0f}</b></div>"
            f'<div style="flex:1;min-width:210px;color:{net_color};font-weight:bold;">'
            f"After-risk value minus investment: {net_sign}EUR {net:,.0f}</div>"
            f"</div>"
        )

        profit_line = ""
        if profitability_pct is not None:
            profit_line = (
                f"<br><b>Probability of positive net value:</b> {profitability_pct:.0%}"
            )

        context_html = (
            f'<div style="margin-top:14px;padding:10px 14px;border-left:4px solid '
            f"{COLORS.warning};background:transparent;color:inherit;font-size:13px;"
            f'line-height:1.6;">'
            f"<b>Largest single risk layer:</b> {dominant_risk}"
            f"{profit_line}"
            f'<div style="margin-top:6px;color:{COLORS.subtle};font-size:12px;">'
            f"These are expected (mean) values across all simulations, not guaranteed "
            f"outcomes and not worst-case losses. Tail risk is shown later as LaR / CVaR."
            f"</div>"
            f"</div>"
        )
        html = (
            f'<div style="border:1px solid {COLORS.border};border-radius:6px;'
            f'padding:18px 22px;margin:12px 0;background:transparent;color:inherit;">'
            f'<h3 style="margin-top:0;color:inherit;font-size:18px;font-weight:bold;">'
            f"{title}</h3>"
            f"{headline_html}{flow_html}{investment_html}{context_html}"
            f"</div>"
        )
        self(html)

    def risk_register_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Risk Register",
    ) -> None:
        """Render risk register table (Risk / Probability / Impact / Loss / Severity / Mitigation)."""
        self.sensitivity(
            rows,
            (
                "Risk",
                "Probability",
                "Impact",
                "Expected Loss",
                "Severity",
                "Mitigation",
            ),
            title=title,
        )

    def portfolio_feature_cards(self, card_data: list[dict]) -> None:
        """Render per-feature risk cards with traffic-light border based on retention %.

        Each card shows: feature name, investment, base BV, final BV, retention %
        traffic-light badge, biggest risk dimension, and recommended action.

        Args:
            card_data: List of dicts with keys name, investment, base_bv, final_bv,
                retention_pct, biggest_risk, action.
        """

        def _card(d: dict) -> str:
            retention = d["retention_pct"]
            if retention >= 60:
                border_color = COLORS.success
                badge_color = COLORS.success
                badge = f"● GREEN ({retention:.0f}%)"
            elif retention >= 30:
                border_color = COLORS.warning
                badge_color = COLORS.warning
                badge = f"● YELLOW ({retention:.0f}%)"
            else:
                border_color = COLORS.danger
                badge_color = COLORS.danger
                badge = f"● RED ({retention:.0f}%)"

            return (
                f'<div style="border:2px solid {border_color};border-radius:6px;'
                f'padding:16px 18px;background:{COLORS.background};flex:1;min-width:220px;">'
                f'<h4 style="margin-top:0;color:{COLORS.neutral};font-size:15px;font-weight:bold;">'
                f"{d['name']}</h4>"
                f'<table style="width:100%;border-collapse:collapse;font-size:12px;line-height:1.7;">'
                f'<tr><td style="color:{COLORS.neutral};">Investment</td>'
                f"<td><b>EUR {d['investment']:,.0f}</b></td></tr>"
                f'<tr><td style="color:{COLORS.neutral};">Base business value</td>'
                f"<td><b>EUR {d['base_bv']:,.0f}</b></td></tr>"
                f'<tr><td style="color:{COLORS.neutral};">Value after all risks</td>'
                f"<td><b>EUR {d['final_bv']:,.0f}</b></td></tr>"
                f'<tr><td style="color:{COLORS.neutral};">Retention</td>'
                f'<td style="color:{badge_color};font-weight:bold;">{badge}</td></tr>'
                f"</table>"
                f'<div style="margin-top:8px;padding:6px 10px;background:{COLORS.surface};'
                f'border-radius:4px;font-size:12px;">'
                f"<b>Biggest risk:</b> {d['biggest_risk']}</div>"
                f'<div style="margin-top:5px;padding:6px 10px;background:{COLORS.surface};'
                f'border-radius:4px;font-size:12px;border-left:3px solid {border_color};">'
                f"<b>Action:</b> {d['action']}</div>"
                f"</div>"
            )

        cards_html = "".join(_card(d) for d in card_data)
        self(
            f'<div style="display:flex;flex-wrap:wrap;gap:12px;margin:10px 0;">'
            f"{cards_html}"
            f"</div>"
        )

    def combined_sensitivity_table(
        self,
        r2_results: dict,
        r3_results: dict,
        r2_levels: list[float],
        r3_levels: list[float],
        *,
        title: str = "Sensitivity — Expected Portfolio Business Value",
    ) -> None:
        """One table showing market and global sensitivity (Low / Baseline / High).

        Replaces the three separate market/global/component tables from the old
        notebook with a single compact 4-column summary.
        """
        r2_sorted = sorted(r2_levels)
        r3_sorted = sorted(r3_levels)
        mid2 = r2_sorted[len(r2_sorted) // 2]
        mid3 = r3_sorted[len(r3_sorted) // 2]

        r2_row = (
            f"Market shock ({r2_sorted[0]:.0%} – {r2_sorted[-1]:.0%})",
            f"EUR {r2_results[r2_sorted[0]].after_risk_3.expected:,.0f}",
            f"EUR {r2_results[mid2].after_risk_3.expected:,.0f}",
            f"EUR {r2_results[r2_sorted[-1]].after_risk_3.expected:,.0f}",
        )
        r3_row = (
            f"Global crisis ({r3_sorted[0]:.1%} – {r3_sorted[-1]:.1%})",
            f"EUR {r3_results[r3_sorted[0]].after_risk_3.expected:,.0f}",
            f"EUR {r3_results[mid3].after_risk_3.expected:,.0f}",
            f"EUR {r3_results[r3_sorted[-1]].after_risk_3.expected:,.0f}",
        )
        self.sensitivity(
            [r2_row, r3_row],
            (
                "Risk Factor",
                "Low (baseline halved)",
                "Baseline",
                "High (baseline ×1.5)",
            ),
            title=title,
        )

    @staticmethod
    def feature_risk_decay(
        feature_names: list[str],
        expected_matrix: list[list[float]],
        layer_labels: list[str] | None = None,
        *,
        title: str = "Feature Business Value Retention Across Risk Layers",
    ) -> None:
        """Render retention-% decay chart with traffic-light background bands."""
        from ..charts.risk import plot_feature_risk_decay

        plot_feature_risk_decay(
            feature_names,
            expected_matrix,
            layer_labels,
            title=title,
        )

    # ------------------------------------------------------------------
    # Composite helpers — reduce notebook cell size
    # ------------------------------------------------------------------

    def feature_risk_profile_cards(
        self,
        features: list[Any],
        feature_profiles: dict[str, Any],
        *,
        layer_attrs: list[str] | None = None,
        layer_names: list[str] | None = None,
    ) -> None:
        """Build and render per-feature risk cards from simulation profiles.

        Computes traffic-light retention, biggest risk dimension, and
        recommended action — moving this logic out of notebook cells.
        """
        _attrs = layer_attrs or [
            "base",
            "after_risk_1",
            "after_risk_2",
            "after_component",
            "after_risk_3",
        ]
        _names = layer_names or ["Base", "Delivery", "Market", "Component", "Global"]
        card_data = []
        for feature in sorted(features, key=lambda f: f.name):
            profile = feature_profiles.get(feature.name)
            if profile is None:
                continue
            base_bv = profile.base.expected
            final_bv = profile.after_risk_3.expected
            retention = (final_bv / base_bv * 100) if base_bv > 0 else 0.0
            layer_values = [getattr(profile, a).expected for a in _attrs]
            deltas = [
                (layer_values[i] - layer_values[i + 1], _names[i + 1])
                for i in range(len(layer_values) - 1)
            ]
            biggest_delta, biggest_name = max(deltas, key=lambda x: x[0])
            if retention >= 60:
                action = "Acceptable risk — proceed with delivery monitoring"
            elif retention >= 30:
                action = (
                    f"Moderate risk — mitigate {biggest_name.lower()} risk "
                    "before full commitment"
                )
            else:
                action = f"High risk — de-risk {biggest_name.lower()} BEFORE committing budget"
            card_data.append(
                {
                    "name": feature.name,
                    "investment": feature.development_cost,
                    "base_bv": base_bv,
                    "final_bv": final_bv,
                    "retention_pct": retention,
                    "biggest_risk": f"{biggest_name} (EUR {biggest_delta:,.0f} lost)",
                    "action": action,
                }
            )
        self.portfolio_feature_cards(card_data)

    def feature_risk_decay_from_profiles(
        self,
        feature_names: list[str],
        feature_profiles: dict[str, Any],
        *,
        layer_labels: list[str] | None = None,
        layer_attrs: list[str] | None = None,
        title: str = "Feature Business Value Retention — Green > 60% · Yellow 30–60% · Red < 30%",
    ) -> None:
        """Render feature risk decay chart from simulation profiles.

        Derives ``expected_matrix`` from profiles so notebooks don't need to
        build the matrix manually.
        """
        _attrs = layer_attrs or [
            "base",
            "after_risk_1",
            "after_risk_2",
            "after_component",
            "after_risk_3",
        ]
        _labels = layer_labels or [
            "Base",
            "After Delivery",
            "After Market",
            "After Component",
            "After Global",
        ]
        short_names = [n.split(": ", 1)[-1] for n in feature_names]
        expected_matrix = [
            [getattr(feature_profiles[f], a).expected for a in _attrs]
            for f in feature_names
        ]
        self.feature_risk_decay(short_names, expected_matrix, _labels, title=title)

    def portfolio_risk_waterfall_detail(
        self,
        portfolio_layers: PortfolioRiskLayers,
        risk_model: ScenarioRiskModel,
        features: list[Any],
        investment: float,
        *,
        waterfall_title: str = "Portfolio Risk Waterfall (ILP-selected features)",
        register_title: str = "Risk Register",
        metrics_title: str = "Portfolio Profitability Assessment",
    ) -> None:
        """Render waterfall table, risk register, chart, and profitability metrics.

        Encapsulates the waterfall row computation, severity classification,
        and risk register formatting that previously lived in notebook cells.
        """
        from ..charts.risk import plot_risk_layer_decay

        waterfall = portfolio_layers.waterfall_summary()
        waterfall_rows = [
            (
                row.layer,
                f"EUR {row.expected:,.0f}",
                "-" if idx == 0 else f"EUR {row.layer_loss:,.0f}",
            )
            for idx, row in enumerate(waterfall.rows)
        ]

        def _severity(loss: float) -> str:
            if loss > 50_000:
                return "CRITICAL"
            if loss > 20_000:
                return "HIGH"
            if loss > 10_000:
                return "MEDIUM"
            return "LOW"

        base_expected = portfolio_layers.base.expected
        after_expected = portfolio_layers.after_risk_3.expected
        delivery_loss = base_expected - portfolio_layers.after_risk_1.expected
        market_loss = (
            portfolio_layers.after_risk_1.expected
            - portfolio_layers.after_risk_2.expected
        )
        component_loss = (
            portfolio_layers.after_risk_2.expected
            - portfolio_layers.after_component.expected
        )
        global_loss = (
            portfolio_layers.after_component.expected
            - portfolio_layers.after_risk_3.expected
        )
        llp_values = [f.likelihood_of_non_delivery for f in features]
        llp_min, llp_max = min(llp_values), max(llp_values)
        comp_probs = list(risk_model.component_risk_by_cluster.values())
        if comp_probs:
            comp_min, comp_max = min(comp_probs), max(comp_probs)
        else:
            fallback_prob = float(risk_model.default_component_probability)
            comp_min = comp_max = fallback_prob
        register_rows = [
            (
                "Delivery",
                f"{llp_min:.0%}–{llp_max:.0%} (per feature)",
                "Total loss",
                f"EUR {delivery_loss:,.0f}",
                _severity(delivery_loss),
                "Reduce LLP",
            ),
            (
                "Market",
                f"{risk_model.risk_2_market_probability:.0%}",
                f"×{risk_model.risk_2_market_multiplier:.2f}",
                f"EUR {market_loss:,.0f}",
                _severity(market_loss),
                "Accept or hedge",
            ),
            (
                "Component",
                f"{comp_min:.0%}–{comp_max:.0%} (per cluster)",
                f"×{risk_model.component_risk_multiplier:.2f}",
                f"EUR {component_loss:,.0f}",
                _severity(component_loss),
                "Platform redundancy",
            ),
            (
                "Global",
                f"{risk_model.risk_3_global_probability:.0%}",
                f"×{risk_model.risk_3_global_multiplier:.2f}",
                f"EUR {global_loss:,.0f}",
                _severity(global_loss),
                "Accept",
            ),
        ]
        self.columns(
            self.sensitivity_html(
                waterfall_rows,
                (
                    RISK_LAYER_LABEL,
                    EXPECTED_BUSINESS_VALUE_LABEL,
                    "Business Value Lost at This Layer",
                ),
                title=waterfall_title,
            ),
            self.sensitivity_html(
                register_rows,
                (
                    "Risk",
                    "Probability",
                    "Impact",
                    "Expected Loss",
                    "Severity",
                    "Mitigation",
                ),
                title=register_title,
            ),
            min_width="380px",
        )
        plot_risk_layer_decay(
            waterfall,
            title="Portfolio Expected Business Value Decay Across Risk Layers",
        )
        net = after_expected - investment
        self.metrics(
            [
                (
                    "Expected business value (after all risks)",
                    f"EUR {after_expected:,.0f}",
                    COLORS.success if after_expected > investment else COLORS.warning,
                ),
                ("Total investment", f"EUR {investment:,.0f}", COLORS.secondary),
                (
                    "Net expected position (business value − investment)",
                    f"EUR {net:,.0f}",
                    COLORS.success if net > 0 else COLORS.danger,
                ),
                (
                    "Business value floor (BVF 95%)",
                    f"EUR {portfolio_layers.after_risk_3.var_95:,.0f}",
                    COLORS.warning,
                ),
            ],
            title=metrics_title,
        )

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

"""Delivery risk stress and assessment domain service."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from fhs.core.model import (
    DeliveryStressResult,
    Feature,
    PnLAssessment,
    PortfolioPnLLayers,
    RiskManagementROI,
    ScenarioRiskModel,
    SimulationResult,
)


class DeliveryRiskService:
    """Domain logic for delivery stress and related business assessments."""

    @staticmethod
    def stress_test_delivery(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel,
        scenarios: int,
        fail_multiplier: float = 1.0,
        delay_multiplier: float = 1.0,
        shock_sensitivity: float = 1.0,
        seed: int = 42,
    ) -> DeliveryStressResult:
        """Simulate delivery execution stress with delay and failure effects."""
        names = list(selected)
        if not names:
            return DeliveryStressResult(
                prob_success=0.0,
                prob_failure=0.0,
                expected_delay_weeks=0.0,
                expected_impact_eur=0.0,
                impact_var_95_eur=0.0,
                impact_cvar_95_eur=0.0,
            )

        n_scenarios = int(scenarios)
        rng = np.random.default_rng(seed)

        market_hit = rng.random(n_scenarios) < risk_model.risk_2_market_probability
        global_hit = rng.random(n_scenarios) < risk_model.risk_3_global_probability

        total_delay_weeks = np.zeros(n_scenarios, dtype=float)
        total_impact = np.zeros(n_scenarios, dtype=float)
        failed_features = np.zeros(n_scenarios, dtype=float)

        for name in names:
            feature = feature_by_name[name]
            planned = feature.development_weeks or max(
                4,
                int(np.ceil(feature.development_cost / 9_000.0)),
            )

            base_fail = float(
                np.clip(
                    feature.likelihood_of_non_delivery * fail_multiplier,
                    0.0,
                    0.95,
                )
            )
            base_delay = float(
                np.clip(
                    (0.12 + 0.58 * feature.likelihood_of_non_delivery)
                    * delay_multiplier,
                    0.0,
                    0.95,
                )
            )

            p_fail = np.clip(
                base_fail + shock_sensitivity * (0.03 * market_hit + 0.10 * global_hit),
                0.0,
                0.98,
            )
            p_delay = np.clip(
                base_delay
                + shock_sensitivity * (0.08 * market_hit + 0.18 * global_hit),
                0.0,
                0.98,
            )

            failed = rng.random(n_scenarios) < p_fail
            delayed = (~failed) & (rng.random(n_scenarios) < p_delay)

            raw_delay = rng.triangular(
                1.0,
                max(2.0, planned * 0.4),
                max(4.0, planned * 1.2),
                size=n_scenarios,
            )
            delay_scale = 1.0 + 0.20 * market_hit + 0.50 * global_hit
            delay_weeks = np.where(delayed, np.rint(raw_delay * delay_scale), 0.0)

            weekly_value = simulation_results[name].expected_business_value / 52.0
            cost_of_delay = delay_weeks * weekly_value
            extra_execution_cost = feature.development_cost * np.clip(
                delay_weeks / max(planned * 2.5, 1.0),
                0.0,
                0.35,
            )
            failure_loss = failed.astype(float) * (
                feature.development_cost
                + 0.55 * simulation_results[name].expected_business_value
            )

            total_delay_weeks += delay_weeks
            total_impact += cost_of_delay + extra_execution_cost + failure_loss
            failed_features += failed.astype(float)

        success = (failed_features == 0) & (total_delay_weeks <= 6)
        failure = (~success) & ((failed_features > 0) | (total_delay_weeks > 14))

        var95 = float(np.percentile(total_impact, 95))
        tail = total_impact[total_impact >= var95]

        return DeliveryStressResult(
            prob_success=float(np.mean(success)),
            prob_failure=float(np.mean(failure)),
            expected_delay_weeks=float(np.mean(total_delay_weeks)),
            expected_impact_eur=float(np.mean(total_impact)),
            impact_var_95_eur=var95,
            impact_cvar_95_eur=float(np.mean(tail)) if len(tail) > 0 else var95,
        )

    @staticmethod
    def risk_management_assessment(
        scenarios: dict[str, DeliveryStressResult],
        *,
        investment: float,
        baseline_label: str = "Baseline",
        managed_label: str = "Managed",
        program_cost_share: float = 0.06,
    ) -> RiskManagementROI:
        """Compare baseline and managed delivery stress to derive ROI metrics."""
        baseline = scenarios.get(baseline_label)
        managed = scenarios.get(managed_label)
        if baseline is None or managed is None:
            return RiskManagementROI(
                program_cost_eur=0.0,
                avoided_expected_loss_eur=0.0,
                net_expected_benefit_eur=0.0,
                tail_risk_reduction_var_95_eur=0.0,
            )

        program_cost = max(0.0, float(program_cost_share)) * max(0.0, float(investment))
        avoided_expected_loss = (
            baseline.expected_impact_eur - managed.expected_impact_eur
        )
        tail_risk_reduction = baseline.impact_var_95_eur - managed.impact_var_95_eur
        return RiskManagementROI(
            program_cost_eur=program_cost,
            avoided_expected_loss_eur=avoided_expected_loss,
            net_expected_benefit_eur=avoided_expected_loss - program_cost,
            tail_risk_reduction_var_95_eur=tail_risk_reduction,
        )

    @staticmethod
    def pnl_assessment(
        pnl_layers: PortfolioPnLLayers,
        *,
        investment: float,
    ) -> PnLAssessment:
        """Assess expected and downside break-even against investment."""
        final_layer = pnl_layers.after_risk_3
        net_expected = final_layer.expected - investment
        net_var_95 = final_layer.var_95 - investment
        return PnLAssessment(
            investment_eur=float(investment),
            expected_business_value_eur=float(final_layer.expected),
            var_95_business_value_eur=float(final_layer.var_95),
            cvar_95_business_value_eur=float(final_layer.cvar_95),
            net_expected_eur=float(net_expected),
            net_var_95_eur=float(net_var_95),
            break_even_expected=net_expected > 0.0,
            break_even_var_95=net_var_95 > 0.0,
        )

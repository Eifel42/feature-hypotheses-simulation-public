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

"""Reporting facade — delegates to focused report modules.

Backward-compatible API: ``PortfolioReportingService`` is the single entry point
used by ``PortfolioAdvisor``. Internally, logic is split across:
- ``year1_risk.py`` — Year-1 Risk reports
- ``po_summary.py`` — PO summary + Markdown formatting
- ``stress_test.py`` — Bundled risk stress tests, executive summary, metadata
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ...model import Feature, SimulationResult
from ..risk import RiskCalculator
from .po_summary import POSummaryReporter
from .stress_test import (
    BundledRiskStressTest,
    ExecutiveSummaryBuilder,
    RunMetadataBuilder,
)
from .year1_risk import Year1RiskReporter


class PortfolioReportingService:
    """Builds PO-facing and Year-1 risk report payloads and text output.

    Thin facade that delegates to:
    - :class:`Year1RiskReporter` for Y1 risk reports
    - :class:`POSummaryReporter` for PO summaries + Markdown
    - :class:`ExecutiveSummaryBuilder` for executive summaries
    - :class:`RunMetadataBuilder` for run metadata
    - :class:`BundledRiskStressTest` for cluster stress tests
    """

    def __init__(self, calculator: RiskCalculator | None = None):
        self.calculator = calculator or RiskCalculator()
        self._year1 = Year1RiskReporter()
        self._po_summary = POSummaryReporter(self.calculator)
        self._executive = ExecutiveSummaryBuilder(self.calculator)
        self._metadata = RunMetadataBuilder()
        self._stress = BundledRiskStressTest(self.calculator)

    def generate_year1_risk_report(self, features: list[Feature]) -> dict[str, Any]:
        """Generate Year-1 Business Value at Risk (Y1 BVaR) and Profit at Risk report."""
        return self._year1.generate_report(features)

    def format_year1_risk_table(self, report: dict[str, Any]) -> str:
        """Format Year-1 Risk Report as text table."""
        return self._year1.format_table(report)

    def format_po_summary_markdown(
        self,
        report: dict[str, Any],
        budget: float | None = None,
    ) -> str:
        """Format PO summary as Markdown report."""
        return self._po_summary.format_markdown(
            report, budget
        )  # pragma: no cover - defensive

    def get_run_metadata(
        self,
        features: list[Feature],
        scenarios: int,
        distribution: str,
        correlation_source: str,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate metadata for transparency and reproducibility."""
        return self._metadata.build(  # pragma: no cover - defensive
            features, scenarios, distribution, correlation_source, seed
        )

    def calculate_bundled_risk_stress_test(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
    ) -> dict[str, Any]:
        """Stress test: all features in same cluster reduced to 50%."""
        return self._stress.calculate(
            features, simulation_results
        )  # pragma: no cover - defensive

    # noinspection PyTypeHintsInspection
    def generate_executive_summary(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        ranking_result: dict[str, Any],
        concentration: dict[str, Any],
        stress_crash: dict[str, Any],
        stress_failure: dict[str, Any],
        metadata: dict[str, Any],
        correlation_matrix: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Generate a comprehensive executive summary."""
        return self._executive.build(  # pragma: no cover - defensive
            features,
            simulation_results,
            ranking_result,
            concentration,
            stress_crash,
            stress_failure,
            metadata,
            correlation_matrix,
        )

    def generate_po_summary(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        ranking_result: dict[str, Any],
        concentration: dict[str, Any],
        robustness_variants: dict[str, Any],
        metadata: dict[str, Any],
        recommended_set: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate Product Owner friendly summary report."""
        return self._po_summary.generate_summary(  # pragma: no cover - defensive
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
            recommended_set,
        )

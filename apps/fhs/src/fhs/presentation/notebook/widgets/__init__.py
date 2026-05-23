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

"""Notebook widget package facade."""

from .cards import (
    detail_card,
    downside_risk_card,
    executive_summary_card,
    feature_risk_card,
    feature_scorecard,
    formula_card,
    portfolio_summary_card,
    section_card,
)
from .comparison import decision_grid, solver_comparison_card
from .facade import FHSDisplay, show
from .portfolio import optimizer_results_card, selection_card
from .primitives import (
    danger_box,
    info_box,
    kpi_card,
    kpi_row,
    note_block,
    section_subheading,
    success_box,
    warning_box,
)
from .tables import (
    backlog_table,
    comparison_table,
    metric_table,
    ranking_table,
    risk_contribution_table,
    sample_table,
    sensitivity_table,
    stress_test_table,
)

__all__ = [
    "FHSDisplay",
    "backlog_table",
    "comparison_table",
    "danger_box",
    "decision_grid",
    "detail_card",
    "downside_risk_card",
    "executive_summary_card",
    "feature_risk_card",
    "feature_scorecard",
    "formula_card",
    "info_box",
    "kpi_card",
    "kpi_row",
    "metric_table",
    "note_block",
    "optimizer_results_card",
    "portfolio_summary_card",
    "ranking_table",
    "risk_contribution_table",
    "sample_table",
    "section_card",
    "section_subheading",
    "selection_card",
    "sensitivity_table",
    "show",
    "solver_comparison_card",
    "stress_test_table",
    "success_box",
    "warning_box",
]

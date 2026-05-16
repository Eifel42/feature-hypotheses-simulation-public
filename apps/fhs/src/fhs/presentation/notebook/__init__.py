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

"""Notebook presentation layer — styling, widgets, and charts for Jupyter.

This package provides styling configuration, HTML widget rendering functions,
reusable Matplotlib chart functions, and data formatters for analysis results.

**Module Layout:**
- `styling.py` – Colour palette, figure sizes, matplotlib configuration
- `widgets/` – HTML rendering functions (cards, tables, grid, display facade)
- `charts/`   – Reusable Matplotlib chart sub-package (distributions, risk, portfolio, forecast)
- `formatters.py` – Data formatters for delivery risk analysis tables

"""

from .charts import (
    plot_beta_sample_size_effect,
    plot_beta_vs_normal_boxplot,
    plot_budget_risk_layers,
    plot_business_value_concentration,
    plot_business_value_forecast,
    plot_delivery_market_resilience,
    plot_distribution_risk_metric_comparison,
    plot_distribution_shape_comparison,
    plot_feature_distributions,
    plot_feature_distributions_interactive,
    plot_feature_ranking,
    plot_llp_impact_bars,
    plot_llp_landscape,
    plot_lognormal_distribution_deep_dive,
    plot_monte_carlo_comparison,
    plot_multi_year_fan,
    plot_multi_year_fan_interactive,
    plot_normal_distribution_deep_dive,
    plot_opportunity_cost,
    plot_portfolio_distribution,
    plot_risk_comparison,
    plot_risk_profile,
    plot_risk_profile_interactive,
    plot_risk_waterfall,
    plot_stress_test,
    plot_uncertainty_comparison,
)
from .styling import (
    COLORS,
    FIG,
    HIST_ALPHA,
    HIST_BINS,
    HIST_EDGE_COLOR,
    HIST_EDGE_WIDTH,
    palette,
    setup_style,
)
from .widgets import show
from .widgets.primitives import info_box, kpi_card

__all__ = [
    # Styling
    "COLORS",
    "FIG",
    "HIST_ALPHA",
    "HIST_BINS",
    "HIST_EDGE_COLOR",
    "HIST_EDGE_WIDTH",
    # Primitive widgets
    "info_box",
    "kpi_card",
    "palette",
    "plot_beta_sample_size_effect",
    "plot_beta_vs_normal_boxplot",
    "plot_budget_risk_layers",
    "plot_business_value_concentration",
    "plot_business_value_forecast",
    "plot_delivery_market_resilience",
    "plot_distribution_risk_metric_comparison",
    "plot_distribution_shape_comparison",
    "plot_feature_distributions",
    "plot_feature_distributions_interactive",
    "plot_feature_ranking",
    "plot_llp_impact_bars",
    "plot_llp_landscape",
    "plot_lognormal_distribution_deep_dive",
    "plot_monte_carlo_comparison",
    "plot_multi_year_fan",
    "plot_multi_year_fan_interactive",
    "plot_normal_distribution_deep_dive",
    "plot_opportunity_cost",
    "plot_portfolio_distribution",
    "plot_risk_comparison",
    # Chart functions
    "plot_risk_profile",
    # Interactive Plotly charts
    "plot_risk_profile_interactive",
    "plot_risk_waterfall",
    "plot_stress_test",
    "plot_uncertainty_comparison",
    "setup_style",
    # Display facade
    "show",
]

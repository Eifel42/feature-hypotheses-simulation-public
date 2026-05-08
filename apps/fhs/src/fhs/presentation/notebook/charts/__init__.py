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

"""Reusable Matplotlib chart functions for Jupyter notebooks.

This package is part of the Presentation Layer.  It encapsulates the
chart-rendering logic so that notebook cells stay concise while the
visual design is defined in one place and covered by unit tests.

**Sub-modules:**
- ``distributions`` – Histogram / distribution charts (risk profile, uncertainty)
- ``risk``          – Risk comparison, stress tests, waterfall, budget layers
- ``portfolio``     – Opportunity cost, feature ranking, business value concentration
- ``forecast``      – Business value forecast, LLP landscape, LLP impact bars
"""

from .capital_budgeting import (
    plot_cashflow_bars,
    plot_npv_comparison,
    plot_npv_rate_curve,
)
from .distributions import (
    plot_beta_sample_size_effect,
    plot_beta_vs_normal_boxplot,
    plot_distribution_risk_metric_comparison,
    plot_distribution_shape_comparison,
    plot_feature_distributions,
    plot_lognormal_distribution_deep_dive,
    plot_monte_carlo_comparison,
    plot_normal_distribution_deep_dive,
    plot_portfolio_distribution,
    plot_risk_profile,
    plot_uncertainty_comparison,
)
from .forecast import (
    plot_business_value_forecast,
    plot_llp_impact_bars,
    plot_llp_landscape,
    plot_multi_year_fan,
)
from .heatmap import plot_correlation_heatmap
from .interactive import (
    plot_feature_distributions_interactive,
    plot_multi_year_fan_interactive,
    plot_risk_profile_interactive,
)
from .portfolio import (
    plot_business_value_concentration,
    plot_feature_ranking,
    plot_opportunity_cost,
    plot_strategy_category_mix,
)
from .risk import (
    plot_budget_risk_layers,
    plot_cost_comparison,
    plot_delivery_market_resilience,
    plot_feature_risk_decay,
    plot_feature_risk_layer_decay,
    plot_profit_histogram,
    plot_risk_comparison,
    plot_risk_layer_decay,
    plot_risk_waterfall,
    plot_runtime_comparison,
    plot_sensitivity_curve,
    plot_sensitivity_panel,
    plot_sprint_delay_grid,
    plot_stress_test,
)

__all__ = [
    "plot_beta_sample_size_effect",
    "plot_beta_vs_normal_boxplot",
    "plot_budget_risk_layers",
    "plot_business_value_concentration",
    "plot_business_value_forecast",
    # capital budgeting
    "plot_cashflow_bars",
    # heatmap
    "plot_correlation_heatmap",
    "plot_cost_comparison",
    "plot_delivery_market_resilience",
    "plot_distribution_risk_metric_comparison",
    "plot_distribution_shape_comparison",
    "plot_feature_distributions",
    "plot_feature_distributions_interactive",
    "plot_feature_ranking",
    # risk
    "plot_feature_risk_decay",
    "plot_feature_risk_layer_decay",
    "plot_llp_impact_bars",
    "plot_llp_landscape",
    "plot_lognormal_distribution_deep_dive",
    # distributions
    "plot_monte_carlo_comparison",
    # forecast / LLP
    "plot_multi_year_fan",
    "plot_multi_year_fan_interactive",
    "plot_normal_distribution_deep_dive",
    "plot_npv_comparison",
    "plot_npv_rate_curve",
    # portfolio
    "plot_opportunity_cost",
    "plot_portfolio_distribution",
    "plot_profit_histogram",
    "plot_risk_comparison",
    "plot_risk_layer_decay",
    "plot_risk_profile",
    # interactive (Plotly)
    "plot_risk_profile_interactive",
    "plot_risk_waterfall",
    "plot_runtime_comparison",
    "plot_sensitivity_curve",
    "plot_sensitivity_panel",
    "plot_sprint_delay_grid",
    "plot_strategy_category_mix",
    "plot_stress_test",
    "plot_uncertainty_comparison",
]

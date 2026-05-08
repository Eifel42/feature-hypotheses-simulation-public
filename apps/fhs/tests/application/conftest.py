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

"""Shared fixtures for application-layer tests."""

import pytest

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.core.model import Feature


@pytest.fixture
def sample_features() -> list[Feature]:
    return [
        Feature(
            name="H1: Simplified UI",
            expected_users=100_000,
            conversion_rate=0.26,
            uncertainty=0.20,
            business_value_per_conversion=4.7,
            development_cost=75_000.0,
            development_weeks=8,
            annual_growth_rate=0.05,
            likelihood_of_non_delivery=0.2,
            dependency_cluster="Customer Experience Platform",
        ),
        Feature(
            name="H2: Traceability",
            expected_users=69_700,
            conversion_rate=0.55,
            uncertainty=0.20,
            business_value_per_conversion=1.77,
            development_cost=50_000.0,
            development_weeks=6,
            annual_growth_rate=0.05,
            likelihood_of_non_delivery=0.5,
            dependency_cluster="Traceability Platform",
        ),
    ]


@pytest.fixture
def risk_model() -> dict[str, object]:
    return {
        "risk_2_market_probability": 0.20,
        "risk_2_market_multiplier": 0.85,
        "risk_3_global_probability": 0.05,
        "risk_3_global_multiplier": 0.60,
        "component_risk_multiplier": 0.70,
        "default_component_probability": 0.08,
        "component_risk_by_cluster": {
            "Customer Experience Platform": 0.08,
            "Traceability Platform": 0.12,
        },
    }


@pytest.fixture
def service(sample_features: list[Feature]) -> AdvancedPortfolioService:
    """Standard AdvancedPortfolioService with 2 000 scenarios for reuse."""
    return AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )

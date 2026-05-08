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

"""Property tests for ranking risk-profile invariants."""

from __future__ import annotations

import itertools

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.portfolio.decision_support import PortfolioDecisionSupportService
from fhs.core.services.risk.calculator import RiskCalculator

_SCENARIO_VALUES = st.lists(
    st.floats(
        min_value=0.0,
        max_value=1_000_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    min_size=300,
    max_size=2_000,
)

_SMALL_SCENARIO_VALUES = st.lists(
    st.floats(
        min_value=0.0,
        max_value=1_000_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    min_size=40,
    max_size=200,
)


@settings(max_examples=30, deadline=None)
@given(scenarios=_SCENARIO_VALUES)
def test_bv_var_matches_percentile_definition(scenarios: list[float]) -> None:
    arr = np.asarray(scenarios, dtype=float)

    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="P",
        bv_scenarios=arr,
        development_cost=1_000.0,
    )
    expected_var = RiskCalculator.calculate_var(arr, confidence_level=0.95)

    assert profile.bv_var == pytest.approx(expected_var)


@settings(max_examples=30, deadline=None)
@given(scenarios=_SCENARIO_VALUES)
def test_convention_invariants_hold(scenarios: list[float]) -> None:
    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="P",
        bv_scenarios=np.asarray(scenarios, dtype=float),
        development_cost=1_000.0,
    )

    assert profile.bv_cvar <= profile.bv_var
    assert profile.loss_cvar >= profile.loss_var


@settings(max_examples=30, deadline=None)
@given(scenarios=_SCENARIO_VALUES)
def test_loss_and_ratio_invariants_hold(scenarios: list[float]) -> None:
    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="P",
        bv_scenarios=np.asarray(scenarios, dtype=float),
        development_cost=1_000.0,
    )

    assert profile.loss_var >= 0.0
    assert 0.0 <= profile.risk_ratio <= 1.0


@settings(max_examples=25, deadline=None)
@given(
    s1=_SMALL_SCENARIO_VALUES,
    s2=_SMALL_SCENARIO_VALUES,
    s3=_SMALL_SCENARIO_VALUES,
    c1=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False),
    c2=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False),
    c3=st.floats(min_value=1.0, max_value=1_000_000.0, allow_nan=False),
)
def test_rankings_are_monotonic_by_strategy(
    s1: list[float],
    s2: list[float],
    s3: list[float],
    c1: float,
    c2: float,
    c3: float,
) -> None:
    features = [
        Feature(
            name="F1",
            expected_users=1_000,
            conversion_rate=0.2,
            uncertainty=0.1,
            development_cost=float(c1),
        ),
        Feature(
            name="F2",
            expected_users=1_000,
            conversion_rate=0.2,
            uncertainty=0.1,
            development_cost=float(c2),
        ),
        Feature(
            name="F3",
            expected_users=1_000,
            conversion_rate=0.2,
            uncertainty=0.1,
            development_cost=float(c3),
        ),
    ]
    arrays = {
        "F1": np.asarray(s1, dtype=float),
        "F2": np.asarray(s2, dtype=float),
        "F3": np.asarray(s3, dtype=float),
    }

    simulation_results = {
        name: SimulationResult(
            feature_name=name,
            results=arr,
            expected_value=float(np.mean(arr)),
            business_value_per_conversion=1.0,
            development_cost=float(
                next(f.development_cost for f in features if f.name == name)
            ),
        )
        for name, arr in arrays.items()
    }

    by_floor = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="var_floor",
    )
    by_ratio = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="risk_ratio",
    )
    by_rorac = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="rorac",
    )
    by_roi = PortfolioDecisionSupportService.rank_features(
        features=features,
        simulation_results=simulation_results,
        strategy="risk_adjusted_roi",
    )

    assert all(
        left.var_95_business_value >= right.var_95_business_value
        for left, right in itertools.pairwise(by_floor)
    )
    assert all(
        left.risk_ratio <= right.risk_ratio
        for left, right in itertools.pairwise(by_ratio)
    )
    assert all(
        left.rorac >= right.rorac for left, right in itertools.pairwise(by_rorac)
    )
    assert all(
        left.risk_adjusted_roi >= right.risk_adjusted_roi
        for left, right in itertools.pairwise(by_roi)
    )

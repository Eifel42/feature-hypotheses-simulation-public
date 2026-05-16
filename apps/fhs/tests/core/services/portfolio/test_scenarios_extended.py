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

"""Extended tests for ScenarioAnalysisService stress test scenarios."""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.portfolio.scenarios import ScenarioAnalysisService
from fhs.core.services.risk.calculator import RiskCalculator


def _feature(name: str, bv: float = 100000, cost: float = 10000) -> Feature:
    return Feature(
        name=name,
        expected_users=10000,
        conversion_rate=0.2,
        business_value_per_conversion=bv / 2000,
        development_cost=cost,
        uncertainty=0.3,
    )


def _sim_result(name: str, mean: float, scenarios: int = 1000) -> SimulationResult:
    rng = np.random.default_rng(42)
    results = rng.normal(mean, mean * 0.1, scenarios)
    return SimulationResult(
        feature_name=name,
        results=results,
        expected_value=mean,
        business_value_per_conversion=5.0,
        development_cost=10000,
    )


def test_stress_test_custom_scenario_requires_multipliers():
    """Test that custom scenario requires custom_multipliers."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1"), _feature("F2")]
    sim_results = {"F1": _sim_result("F1", 50000), "F2": _sim_result("F2", 30000)}

    with pytest.raises(ValueError, match="custom_multipliers required"):
        service.stress_test(
            features=features,
            simulation_results=sim_results,
            scenario="custom",
        )


def test_stress_test_unknown_scenario_raises():
    """Test that unknown scenario name raises ValueError."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1")]
    sim_results = {"F1": _sim_result("F1", 50000)}

    with pytest.raises(ValueError, match="Unknown scenario"):
        service.stress_test(
            features=features,
            simulation_results=sim_results,
            scenario="invalid_scenario",
        )


def test_stress_test_market_crash_scenario():
    """Test market crash scenario applies 50% multiplier to all features."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1"), _feature("F2")]
    sim_results = {"F1": _sim_result("F1", 50000), "F2": _sim_result("F2", 30000)}

    result = service.stress_test(
        features=features,
        simulation_results=sim_results,
        scenario="market_crash",
    )

    assert result["scenario"] == "Market Crash (50%)"
    assert result["multipliers"]["F1"] == 0.5
    assert result["multipliers"]["F2"] == 0.5


def test_stress_test_feature_failure_scenario():
    """Test feature_failure scenario targets highest-value feature."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1"), _feature("F2")]
    sim_results = {
        "F1": _sim_result("F1", 50000),  # Higher value
        "F2": _sim_result("F2", 30000),
    }

    result = service.stress_test(
        features=features,
        simulation_results=sim_results,
        scenario="feature_failure",
    )

    assert "Feature Failure: F1" in result["scenario"]
    assert result["multipliers"]["F1"] == 0.2


def test_stress_test_best_case_scenario():
    """Test best_case scenario applies 150% multiplier to all features."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1"), _feature("F2")]
    sim_results = {"F1": _sim_result("F1", 50000), "F2": _sim_result("F2", 30000)}

    result = service.stress_test(
        features=features,
        simulation_results=sim_results,
        scenario="best_case",
    )

    assert result["scenario"] == "Best Case (150%)"
    assert result["multipliers"]["F1"] == 1.5
    assert result["multipliers"]["F2"] == 1.5


def test_stress_test_custom_scenario_with_multipliers():
    """Test custom scenario with provided multipliers."""
    calc = RiskCalculator()
    service = ScenarioAnalysisService(calculator=calc)
    features = [_feature("F1"), _feature("F2")]
    sim_results = {"F1": _sim_result("F1", 50000), "F2": _sim_result("F2", 30000)}

    result = service.stress_test(
        features=features,
        simulation_results=sim_results,
        scenario="custom",
        custom_multipliers={"F1": 0.8, "F2": 1.2},
    )

    assert result["scenario"] == "Custom"
    assert result["multipliers"]["F1"] == 0.8
    assert result["multipliers"]["F2"] == 1.2

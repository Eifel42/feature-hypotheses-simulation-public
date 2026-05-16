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

"""Tests for governance value objects."""

from __future__ import annotations

from fhs.core.model.value_objects.governance import ModelCard


def test_model_card_summary_lines_with_owner():
    """Test ModelCard.summary_lines() when owner is set."""
    card = ModelCard(owner="Product Management")
    lines = card.summary_lines()
    assert any("**Owner:** Product Management" in line for line in lines)
    assert any("**Model:**" in line for line in lines)


def test_model_card_summary_lines_without_owner():
    """Test ModelCard.summary_lines() when owner is empty (default)."""
    card = ModelCard()
    lines = card.summary_lines()
    # Should not include owner line when empty
    assert not any("**Owner:**" in line for line in lines)
    assert any("**Model:**" in line for line in lines)
    assert any("**Purpose:**" in line for line in lines)


def test_decision_policy_evaluate_portfolio_review_grade():
    """Test RiskAppetitePolicy.evaluate_portfolio with multiple failures (REVIEW grade)."""
    from fhs.core.model.value_objects.governance import (
        DecisionGrade,
        RiskAppetitePolicy,
    )

    policy = RiskAppetitePolicy(
        min_break_even_probability=0.75,
        min_bvf_ratio=0.80,
        max_cvar_loss=10_000.0,
        max_cluster_concentration=0.5,
    )

    # Create a result that fails multiple checks
    result = policy.evaluate_portfolio(
        break_even_probability=0.50,  # Below min
        bvf_95=0.60,  # Below min
        expected_value=100_000.0,
        cvar_loss=20_000.0,  # Above max
        cluster_concentration=0.7,  # Above max
    )

    # Should be REVIEW because total_fails > 1
    assert result.grade == DecisionGrade.REVIEW
    assert len(result.reasons) >= 2

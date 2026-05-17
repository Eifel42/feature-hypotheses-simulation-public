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

"""Tests for executive decision value objects."""

from __future__ import annotations

from fhs.core.model.value_objects.executive_decision import (
    CONDITIONAL_GO,
    GO,
    REVIEW,
    DecisionDimension,
    aggregate_decision_signals,
)


def test_aggregate_decision_signals_all_go_returns_go():
    """Aggregate result is GO when all dimensions are GO."""
    dimensions = (
        DecisionDimension("Business Value", GO, "NPV", "Strong upside"),
        DecisionDimension("Risk", GO, "LaR", "Tail risk acceptable"),
    )

    result = aggregate_decision_signals(dimensions)

    assert result.overall_signal == GO
    assert result.strengths == ("Business Value", "Risk")
    assert result.attention_needed == ()


def test_aggregate_decision_signals_two_reviews_returns_review():
    """Aggregate result is REVIEW when at least two dimensions are REVIEW."""
    dimensions = (
        DecisionDimension("Business Value", REVIEW, "BVF 95%", "Weak floor"),
        DecisionDimension("Delivery", REVIEW, "Delay", "High overrun risk"),
        DecisionDimension("Portfolio Fit", GO, "Score", "Aligned"),
    )

    result = aggregate_decision_signals(dimensions)

    assert result.overall_signal == REVIEW
    assert result.strengths == ("Portfolio Fit",)
    assert result.attention_needed == (
        "Business Value",
        "Delivery",
    )


def test_decision_result_counts_include_all_signal_types():
    """Count properties expose GO/CONDITIONAL_GO/REVIEW totals correctly."""
    dimensions = (
        DecisionDimension("Business Value", GO, "Expected", "Positive"),
        DecisionDimension("Risk", CONDITIONAL_GO, "CVaR", "Needs guardrails"),
        DecisionDimension("Delivery", REVIEW, "Break-even", "Below target"),
    )

    result = aggregate_decision_signals(dimensions)

    assert result.overall_signal == CONDITIONAL_GO
    assert result.go_count == 1
    assert result.conditional_count == 1
    assert result.review_count == 1

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

"""Tests for governance domain value objects."""

import pytest

from fhs.core.model.value_objects.governance import (
    AssumptionConfidence,
    AssumptionMetadata,
    AssumptionStatus,
    DecisionGrade,
    DecisionPolicy,
    DecisionPolicyResult,
    ModelCard,
    RiskAppetitePolicy,
)

# ---------------------------------------------------------------------------
# AssumptionMetadata
# ---------------------------------------------------------------------------


class TestAssumptionMetadata:
    def test_defaults(self):
        meta = AssumptionMetadata()
        assert meta.source == ""
        assert meta.confidence == AssumptionConfidence.LOW
        assert meta.status == AssumptionStatus.PLACEHOLDER
        assert not meta.is_decision_grade

    def test_from_dict_full(self):
        raw = {
            "source": "user research panel",
            "owner": "product analytics",
            "confidence": "medium",
            "status": "reviewed",
            "last_reviewed": "2026-04-27",
            "notes": "n=200",
        }
        meta = AssumptionMetadata.from_dict(raw)
        assert meta.source == "user research panel"
        assert meta.owner == "product analytics"
        assert meta.confidence == AssumptionConfidence.MEDIUM
        assert meta.status == AssumptionStatus.REVIEWED
        assert meta.last_reviewed == "2026-04-27"
        assert meta.notes == "n=200"

    def test_from_dict_missing_keys_use_defaults(self):
        meta = AssumptionMetadata.from_dict({})
        assert meta.confidence == AssumptionConfidence.LOW
        assert meta.status == AssumptionStatus.PLACEHOLDER

    def test_is_decision_grade_reviewed(self):
        meta = AssumptionMetadata(status=AssumptionStatus.REVIEWED)
        assert meta.is_decision_grade

    def test_is_decision_grade_validated(self):
        meta = AssumptionMetadata(status=AssumptionStatus.VALIDATED)
        assert meta.is_decision_grade

    def test_is_decision_grade_false_for_placeholder(self):
        meta = AssumptionMetadata(status=AssumptionStatus.PLACEHOLDER)
        assert not meta.is_decision_grade

    def test_is_decision_grade_false_for_expert_estimate(self):
        meta = AssumptionMetadata(status=AssumptionStatus.EXPERT_ESTIMATE)
        assert not meta.is_decision_grade

    def test_frozen(self):
        meta = AssumptionMetadata()
        with pytest.raises(Exception):
            meta.source = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# DecisionPolicy
# ---------------------------------------------------------------------------


class TestDecisionPolicy:
    def test_defaults(self):
        policy = DecisionPolicy()
        assert policy.min_break_even_probability == 0.60
        assert policy.min_bvf_ratio == 0.70
        assert policy.require_assumption_status is None

    def test_from_dict(self):
        policy = DecisionPolicy.from_dict(
            {
                "min_break_even_probability": 0.75,
                "min_bvf_ratio": 0.80,
                "require_assumption_status": "reviewed",
            }
        )
        assert policy.min_break_even_probability == 0.75
        assert policy.min_bvf_ratio == 0.80
        assert policy.require_assumption_status == AssumptionStatus.REVIEWED

    def test_from_dict_empty_uses_defaults(self):
        policy = DecisionPolicy.from_dict({})
        assert policy.min_break_even_probability == 0.60
        assert policy.require_assumption_status is None

    def test_evaluate_go_all_pass(self):
        policy = DecisionPolicy(min_break_even_probability=0.60, min_bvf_ratio=0.70)
        result = policy.evaluate(
            break_even_probability=0.80,
            bvf_95=8_000,
            expected_value=10_000,
        )
        assert result.grade == DecisionGrade.GO
        assert result.passed
        assert len(result.reasons) == 0

    def test_evaluate_review_both_fail(self):
        policy = DecisionPolicy(min_break_even_probability=0.80, min_bvf_ratio=0.90)
        result = policy.evaluate(
            break_even_probability=0.50,
            bvf_95=5_000,
            expected_value=10_000,
        )
        assert result.grade == DecisionGrade.REVIEW
        assert not result.passed
        assert len(result.reasons) == 2

    def test_evaluate_conditional_go_one_fail(self):
        policy = DecisionPolicy(min_break_even_probability=0.80, min_bvf_ratio=0.70)
        result = policy.evaluate(
            break_even_probability=0.50,
            bvf_95=8_000,
            expected_value=10_000,
        )
        assert result.grade == DecisionGrade.CONDITIONAL_GO

    def test_evaluate_assumption_status_below_required(self):
        policy = DecisionPolicy(
            min_break_even_probability=0.60,
            min_bvf_ratio=0.70,
            require_assumption_status=AssumptionStatus.REVIEWED,
        )
        result = policy.evaluate(
            break_even_probability=0.80,
            bvf_95=8_000,
            expected_value=10_000,
            assumption_status=AssumptionStatus.PLACEHOLDER,
        )
        assert result.grade == DecisionGrade.CONDITIONAL_GO
        assert any("Assumption" in r for r in result.reasons)

    def test_evaluate_assumption_status_meets_required(self):
        policy = DecisionPolicy(
            min_break_even_probability=0.60,
            require_assumption_status=AssumptionStatus.REVIEWED,
        )
        result = policy.evaluate(
            break_even_probability=0.80,
            bvf_95=8_000,
            expected_value=10_000,
            assumption_status=AssumptionStatus.VALIDATED,
        )
        assert result.grade == DecisionGrade.GO

    def test_evaluate_skips_bvf_check_when_expected_value_zero(self):
        policy = DecisionPolicy(min_break_even_probability=0.60, min_bvf_ratio=0.70)
        result = policy.evaluate(
            break_even_probability=0.80,
            bvf_95=0,
            expected_value=0,
        )
        assert result.grade == DecisionGrade.GO

    def test_evaluate_multiple_failures_returns_review(self):
        """Multiple failures (total_fails > 1) result in REVIEW grade."""
        policy = DecisionPolicy(min_break_even_probability=0.80, min_bvf_ratio=0.90)
        result = policy.evaluate(
            break_even_probability=0.50,  # Fails
            bvf_95=5_000,
            expected_value=10_000,  # bvf_ratio = 0.5, fails
        )
        assert result.grade == DecisionGrade.REVIEW
        assert len(result.reasons) >= 2


# ---------------------------------------------------------------------------
# RiskAppetitePolicy
# ---------------------------------------------------------------------------


class TestRiskAppetitePolicy:
    def test_defaults(self):
        policy = RiskAppetitePolicy()
        assert policy.min_break_even_probability == 0.70
        assert policy.min_bvf_ratio == 0.80
        assert policy.max_cvar_loss is None
        assert policy.max_cluster_concentration is None
        assert policy.max_sunk_cost_at_cancellation is None

    def test_from_dict_full(self):
        policy = RiskAppetitePolicy.from_dict(
            {
                "min_break_even_probability": 0.75,
                "min_bvf_ratio": 0.85,
                "max_cvar_loss": 50_000,
                "max_cluster_concentration": 0.40,
                "max_sunk_cost_at_cancellation": 30_000,
                "require_assumption_status": "reviewed",
            }
        )
        assert policy.max_cvar_loss == 50_000.0
        assert policy.max_cluster_concentration == 0.40
        assert policy.max_sunk_cost_at_cancellation == 30_000.0
        assert policy.require_assumption_status == AssumptionStatus.REVIEWED

    def test_as_decision_policy_inherits_thresholds(self):
        rap = RiskAppetitePolicy(min_break_even_probability=0.75, min_bvf_ratio=0.85)
        dp = rap.as_decision_policy()
        assert isinstance(dp, DecisionPolicy)
        assert dp.min_break_even_probability == 0.75
        assert dp.min_bvf_ratio == 0.85

    def test_evaluate_portfolio_go(self):
        policy = RiskAppetitePolicy(
            min_break_even_probability=0.70,
            min_bvf_ratio=0.80,
            max_cvar_loss=50_000,
        )
        result = policy.evaluate_portfolio(
            break_even_probability=0.85,
            bvf_95=9_000,
            expected_value=10_000,
            cvar_loss=20_000,
        )
        assert result.grade == DecisionGrade.GO

    def test_evaluate_portfolio_cvar_breach(self):
        policy = RiskAppetitePolicy(max_cvar_loss=50_000)
        result = policy.evaluate_portfolio(
            break_even_probability=0.85,
            bvf_95=9_000,
            expected_value=10_000,
            cvar_loss=80_000,
        )
        assert result.grade != DecisionGrade.GO
        assert any("CVaR" in r for r in result.reasons)

    def test_evaluate_portfolio_cluster_concentration_breach(self):
        policy = RiskAppetitePolicy(max_cluster_concentration=0.40)
        result = policy.evaluate_portfolio(
            break_even_probability=0.85,
            bvf_95=9_000,
            expected_value=10_000,
            cluster_concentration=0.60,
        )
        assert any("concentration" in r for r in result.reasons)

    def test_evaluate_portfolio_sunk_cost_breach(self):
        policy = RiskAppetitePolicy(max_sunk_cost_at_cancellation=30_000)
        result = policy.evaluate_portfolio(
            break_even_probability=0.85,
            bvf_95=9_000,
            expected_value=10_000,
            sunk_cost=50_000,
        )
        assert any("Sunk cost" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# ModelCard
# ---------------------------------------------------------------------------


class TestModelCard:
    def test_defaults(self):
        card = ModelCard()
        assert card.model_name == "Feature Hypotheses Simulation"
        assert card.version == "1.0.0"
        assert "Monte Carlo" in card.purpose
        assert len(card.approved_use) > 0
        assert len(card.limitations) > 0
        assert card.owner == ""

    def test_summary_lines_contains_key_fields(self):
        card = ModelCard(owner="Risk Management Office")
        lines = card.summary_lines()
        full_text = "\n".join(lines)
        assert "Feature Hypotheses Simulation" in full_text
        assert "1.0.0" in full_text
        assert "Risk Management Office" in full_text
        assert "Approved use" in full_text
        assert "Limitations" in full_text

    def test_frozen(self):
        card = ModelCard()
        with pytest.raises(Exception):
            card.model_name = "changed"  # type: ignore[misc]

    def test_custom_fields(self):
        card = ModelCard(
            model_name="Custom Model",
            version="2.0.0",
            owner="Analytics Team",
        )
        assert card.model_name == "Custom Model"
        assert card.version == "2.0.0"
        assert card.owner == "Analytics Team"


# ---------------------------------------------------------------------------
# DecisionPolicyResult
# ---------------------------------------------------------------------------


class TestDecisionPolicyResult:
    def test_passed_true_for_go(self):
        result = DecisionPolicyResult(grade=DecisionGrade.GO, reasons=())
        assert result.passed

    def test_passed_false_for_conditional_go(self):
        result = DecisionPolicyResult(
            grade=DecisionGrade.CONDITIONAL_GO, reasons=("reason",)
        )
        assert not result.passed

    def test_passed_false_for_review(self):
        result = DecisionPolicyResult(grade=DecisionGrade.REVIEW, reasons=("r1", "r2"))
        assert not result.passed

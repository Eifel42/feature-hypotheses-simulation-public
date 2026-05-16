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

"""Tests for financial view value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import IrrAssessment, NpvAssessment


def test_npv_assessment_is_immutable() -> None:
    assessment = NpvAssessment(
        verdict="GO",
        primary_message="positive",
        downside_message=None,
        positive_expected=True,
        downside_risk=False,
    )

    with pytest.raises(FrozenInstanceError):
        assessment.verdict = "REVIEW"


def test_irr_assessment_fields() -> None:
    assessment = IrrAssessment(
        verdict="CONDITIONAL_GO",
        primary_message="near hurdle",
        downside_message="floor below hurdle",
        margin_to_discount_rate=0.01,
        expected_above_hurdle=True,
        downside_below_hurdle=True,
    )

    assert assessment.verdict == "CONDITIONAL_GO"
    assert assessment.downside_below_hurdle is True

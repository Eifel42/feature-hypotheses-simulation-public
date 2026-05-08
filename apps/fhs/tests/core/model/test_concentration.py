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

"""Tests for concentration value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import ConcentrationResult


def test_concentration_result_is_immutable() -> None:
    result = ConcentrationResult(
        hhi=0.24,
        shares={"H1": 0.4, "H2": 0.35, "H3": 0.25},
        verdict="Moderate concentration",
    )

    with pytest.raises(FrozenInstanceError):
        result.verdict = "Low concentration"


def test_concentration_result_fields() -> None:
    result = ConcentrationResult(
        hhi=0.28,
        shares={"H1": 0.55, "H2": 0.30, "H3": 0.15},
        verdict="High concentration",
    )

    assert sum(result.shares.values()) == pytest.approx(1.0)
    assert result.hhi >= 0.25

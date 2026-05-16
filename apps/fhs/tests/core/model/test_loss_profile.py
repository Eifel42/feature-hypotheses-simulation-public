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

"""Tests for loss profile value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import LossMetrics, LossProfile


def test_loss_profile_is_immutable() -> None:
    profile = LossProfile(
        confidence=0.95,
        pnl_expected=120_000.0,
        pnl_var=80_000.0,
        pnl_cvar=70_000.0,
        loss_expected=20_000.0,
        loss_var=40_000.0,
        loss_cvar=55_000.0,
        worst_case_loss=90_000.0,
    )

    with pytest.raises(FrozenInstanceError):
        profile.confidence = 0.99


def test_loss_metrics_fields() -> None:
    profile = LossProfile(
        confidence=0.95,
        pnl_expected=120_000.0,
        pnl_var=80_000.0,
        pnl_cvar=70_000.0,
        loss_expected=20_000.0,
        loss_var=40_000.0,
        loss_cvar=55_000.0,
        worst_case_loss=90_000.0,
    )
    metrics = LossMetrics(
        year1=profile,
        catastrophe_threshold=150_000.0,
        catastrophe_probability=0.08,
        cvar_loss=55_000.0,
        investment=140_000.0,
    )

    assert metrics.year1.loss_cvar == 55_000.0
    assert metrics.catastrophe_probability == pytest.approx(0.08)

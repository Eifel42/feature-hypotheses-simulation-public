#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Tests for scenario reduction utility used by CVaR-MILP."""

from __future__ import annotations

import sys

import numpy as np
import pytest

from fhs.core.services.optimization.risk.scenario_reduction import reduce_scenarios


def _feature_scenarios(seed: int = 42, n: int = 500) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    return {
        "A": rng.normal(120.0, 15.0, size=n),
        "B": rng.normal(90.0, 25.0, size=n),
        "C": rng.normal(70.0, 20.0, size=n),
    }


def test_reduce_scenarios_returns_expected_shapes_and_weights():
    scenarios = _feature_scenarios()

    reduced, weights = reduce_scenarios(scenarios, n_reduced=25, seed=7)

    assert reduced.shape == (25, 3)
    assert weights.shape == (25,)
    assert np.all(weights >= 0.0)
    assert np.sum(weights) == pytest.approx(1.0)


def test_reduce_scenarios_is_deterministic_with_fixed_seed():
    scenarios = _feature_scenarios(seed=123)

    reduced_1, weights_1 = reduce_scenarios(scenarios, n_reduced=30, seed=99)
    reduced_2, weights_2 = reduce_scenarios(scenarios, n_reduced=30, seed=99)

    np.testing.assert_allclose(reduced_1, reduced_2)
    np.testing.assert_allclose(weights_1, weights_2)


def test_reduce_scenarios_raises_for_empty_input():
    with pytest.raises(ValueError, match="must not be empty"):
        reduce_scenarios({})


def test_reduce_scenarios_raises_when_sklearn_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "sklearn", None)
    monkeypatch.setitem(sys.modules, "sklearn.cluster", None)

    with pytest.raises(ImportError, match="scikit-learn"):
        reduce_scenarios({"A": np.array([1.0, 2.0, 3.0])}, n_reduced=1)

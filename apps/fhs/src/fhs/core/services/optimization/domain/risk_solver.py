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

"""Risk-aware optimization solver protocol."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget
from fhs.core.services.optimization.domain.portfolio_result import PortfolioResult


@runtime_checkable
class RiskSolver(Protocol):
    """Protocol for solvers that optimize directly on scenario distributions."""

    # noinspection PyTypeHintsInspection
    def solve(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        budget: float | Budget,
        alpha: float = 0.95,
        *,
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
    ) -> PortfolioResult:
        """Find a budget-feasible feature set optimizing a risk objective."""
        ...

    @property
    def name(self) -> str:
        """Solver name for reporting and diagnostics."""
        ...

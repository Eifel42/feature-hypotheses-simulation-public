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

"""OptimizationStrategy Value Object — portfolio optimization objectives."""

from enum import StrEnum


class OptimizationStrategy(StrEnum):
    """
    Portfolio Optimization Strategy.

    Defines the objective function for portfolio optimization.
    """

    VAR_FLOOR = "var_floor"
    """Maximize VaR95 (worst-case business value at 95% confidence)."""

    EXPECTED = "expected"
    """Maximize expected portfolio business value."""

    SHARPE = "sharpe"
    """Maximize Sharpe ratio (expected return / risk)."""

    NPV_YEAR1 = "npv_year1"
    """Maximize Year-1 NPV (discounted expected revenue minus investment)."""

    NPV_3YEAR = "npv_3year"
    """Maximize 3-year NPV (discounted growth-adjusted revenue minus investment)."""

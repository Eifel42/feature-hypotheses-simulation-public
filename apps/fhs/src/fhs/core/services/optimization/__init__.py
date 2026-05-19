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

"""
Portfolio Optimization Module

DDD-based architecture with separated concerns:
- Domain: Protocols and Value Objects
- Solvers: Concrete implementations (Exact, Greedy, ILP)
- Scoring: Strategy pattern for objective functions
- Risk: Delivery risk analysis
"""

from fhs.core.services.optimization.domain import (
    PortfolioResult,
    PortfolioSolver,
    RiskSolver,
)
from fhs.core.services.optimization.risk import DeliveryRiskAnalyzer
from fhs.core.services.optimization.scoring import (
    ObjectiveFunction,
    ObjectiveFunctionFactory,
    PortfolioMetrics,
    PortfolioMetricsCalculator,
)
from fhs.core.services.optimization.solvers import (
    CVaRMILPSolver,
    ExactSolver,
    GreedySolver,
    ILPSolver,
)

__all__ = [
    "CVaRMILPSolver",
    # Risk
    "DeliveryRiskAnalyzer",
    # Solvers
    "ExactSolver",
    "GreedySolver",
    "ILPSolver",
    # Scoring
    "ObjectiveFunction",
    "ObjectiveFunctionFactory",
    "PortfolioMetrics",
    "PortfolioMetricsCalculator",
    "PortfolioResult",
    # Domain
    "PortfolioSolver",
    "RiskSolver",
]

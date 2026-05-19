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
Simulation Configuration Value Object

Domain-specific configuration for Monte Carlo simulation, risk metrics,
and numerical parameters. This is domain logic, not infrastructure.
"""

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Central simulation configuration.

    Groups all tuneable parameters for Monte Carlo simulation, risk metrics,
    bootstrap analysis, logging, numerical precision, and caching.

    This is a Domain Value Object representing simulation parameters,
    not infrastructure configuration.
    """

    # Monte Carlo Simulation Defaults
    MIN_SCENARIOS: int = 1000
    DEFAULT_SCENARIOS: int = 10000

    # Uncertainty interpretation: how many standard deviations span the full
    # uncertainty range.  The default value of 3.0 implements the 3-sigma rule
    # (99.7 % confidence interval).
    #
    # Concretely: std_dev = mean × uncertainty / UNCERTAINTY_SIGMA_RANGE
    #
    # Example — uncertainty = 0.3 with default 3.0:
    #   std_dev = mean × 0.3 / 3.0 = mean × 0.1
    #   → 99.7 % of simulated values fall within ±30 % of the mean (±3σ)
    #
    # ⚠️  Common misread: uncertainty is NOT a ±1σ band.
    #   uncertainty = 0.3  means  ±3σ spans ±30 %  (NOT ±1σ spans ±30 %)
    #   A user who mistakes this for ±1σ will under-estimate tail risk by 9×.
    UNCERTAINTY_SIGMA_RANGE: float = 3.0  # 3-sigma rule: 99.7 % confidence

    # Risk Metrics & Confidence Levels
    DEFAULT_CI_LEVEL: float = 0.95

    # Bootstrap Configuration
    BOOTSTRAP_SAMPLES: int = 1000
    BOOTSTRAP_CI_LEVEL: float = 0.95

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str | None = None  # None = console only
    LOG_JSON: bool = False  # Structured JSON logging

    # Numerical Precision
    FLOAT_TOLERANCE: float = 1e-10
    MIN_PROBABILITY: float = 0.001
    MAX_PROBABILITY: float = 0.999

    # Distribution Defaults
    DEFAULT_DISTRIBUTION: str = "normal"
    ALLOWED_DISTRIBUTIONS: list[str] | None = None

    # Data Validation
    MAX_FEATURE_USERS: int = 1_000_000_000  # 1 billion max
    MIN_FEATURE_USERS: int = 1
    CONVERSION_RATE_DECIMALS: int = 4
    UNCERTAINTY_DECIMALS: int = 4

    # Performance
    ENABLE_CACHING: bool = True
    CACHE_MAX_SIZE: int = 128

    # Numerical Derivatives
    MARGINAL_RISK_EPSILON: float = 0.01

    def __post_init__(self):
        """Initialize default values"""
        if self.ALLOWED_DISTRIBUTIONS is None:
            self.ALLOWED_DISTRIBUTIONS = [
                "normal",
                "uniform",
                "lognormal",
                "beta",
                "truncnorm",
            ]


# Global default instance
DEFAULT_CONFIG = SimulationConfig()

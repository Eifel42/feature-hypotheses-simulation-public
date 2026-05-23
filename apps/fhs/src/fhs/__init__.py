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
Feature Hypotheses Simulation

Democratizing Financial Risk Management for Product Development

Copyright (c) 2025 eifel42.dev

MIT License — see LICENSE file for details.

This is a prototype for educational and research purposes.
Provided "as is" without warranty of any kind.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__version__ = "1.3.0"
__license__ = "MIT"
__copyright__ = "Copyright 2025 eifel42.dev"

import logging
import logging.config

from .core.model import Feature
from .core.model.exceptions import (
    FHSException,
    SimulationError,
    ValidationError,
)
from .core.model.value_objects import BetaParameters, FeatureRankingMetrics
from .core.model.value_objects.governance import (
    AssumptionConfidence,
    AssumptionMetadata,
    AssumptionStatus,
    DecisionGrade,
    DecisionPolicy,
    DecisionPolicyResult,
    ModelCard,
    RiskAppetitePolicy,
)
from .core.services.simulation.simulator import FeatureSimulator
from .infra.config import DEFAULT_CONFIG
from .ux_simulation import (
    TaskComplexity,
    TaskScenario,
    UserProfile,
    UserSurveySimulator,
    UserType,
    UXSimulator,
)

if TYPE_CHECKING:
    from .infra.config import SimulationConfig

from . import examples  # noqa: F401 — make fhs.examples importable


# noinspection PyTypeHintsInspection
def configure_logging(config: SimulationConfig | None = None) -> logging.Logger:
    """
    Configure structured logging for the FHS system

    Args:
        config: SimulationConfig with logging settings (None = DEFAULT_CONFIG)

    Returns:
        Root logger for the FHS package
    """
    if config is None:
        config = DEFAULT_CONFIG

    _fhs_logger = logging.getLogger("fhs")
    # Clear existing handlers to prevent duplicates on repeated calls
    for h in list(_fhs_logger.handlers):
        h.close()
        _fhs_logger.removeHandler(h)
    _fhs_logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # Handler: Console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    formatter = logging.Formatter(config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    _fhs_logger.addHandler(console_handler)

    # Handler: File (if configured)
    if config.LOG_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
        file_handler.setFormatter(formatter)
        _fhs_logger.addHandler(file_handler)

    return _fhs_logger


# Module-level logger — no handlers installed at import time.
# Call configure_logging() explicitly in applications if needed.
logger = logging.getLogger("fhs")

__all__ = [
    "DEFAULT_CONFIG",
    "AssumptionConfidence",
    "AssumptionMetadata",
    "AssumptionStatus",
    "BetaParameters",
    "DecisionGrade",
    "DecisionPolicy",
    "DecisionPolicyResult",
    "FHSException",
    "Feature",
    "FeatureRankingMetrics",
    "FeatureSimulator",
    "ModelCard",
    "RiskAppetitePolicy",
    "SimulationError",
    "TaskComplexity",
    "TaskScenario",
    "UXSimulator",
    "UserProfile",
    "UserSurveySimulator",
    "UserType",
    "ValidationError",
    "configure_logging",
    "logger",
]

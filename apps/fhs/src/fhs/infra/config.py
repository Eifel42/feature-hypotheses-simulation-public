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
Infrastructure Configuration Module

Provides infrastructure-specific configuration (logging, I/O, external systems).
Domain configuration (SimulationConfig) has been moved to fhs.core.model.

DEPRECATED: Re-exports for backward compatibility.
"""

import logging
import sys

# Re-export domain config for backward compatibility
from fhs.core.model.value_objects.simulation_config import (
    DEFAULT_CONFIG,
    SimulationConfig,
)

__all__ = ["DEFAULT_CONFIG", "SimulationConfig", "setup_logging"]


def setup_logging(
    level: str = "INFO",
    log_format: str | None = None,
    log_file: str | None = None,
    log_json: bool = False,
) -> None:
    """
    Configure logging for the application.

    This is infrastructure concern (I/O, formatting, handlers).

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Optional file path for logging
        log_json: Enable JSON structured logging
    """
    if log_format is None:
        log_format = DEFAULT_CONFIG.LOG_FORMAT

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    # JSON logging would require additional library (e.g., python-json-logger)
    if log_json:
        logging.warning("JSON logging not yet implemented")

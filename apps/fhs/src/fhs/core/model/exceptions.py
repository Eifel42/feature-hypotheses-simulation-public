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
Custom Exception Hierarchy for Feature Hypotheses Simulation

Provides structured error handling with clear error messages and remediation advice.
"""

from typing import Any


class FHSException(Exception):
    """Base exception for all FHS errors.

    Carries a human-readable *message* and an optional *details* dict
    for structured error context.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """
        Initialize FHS Exception

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation with details"""
        if self.details:
            details_str = "\nDetails: " + ", ".join(
                f"{k}={v}" for k, v in self.details.items()
            )
            return f"{self.message}{details_str}"
        return self.message


class ValidationError(FHSException):
    """Raised when input validation fails (invalid field values, ranges, etc.)."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ):
        """
        Initialize Validation Error

        Args:
            message: Error message
            field: Field that failed validation
            value: The invalid value
            **kwargs: Additional details
        """
        details = {"field": field, "value": value, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class SimulationError(FHSException):
    """Raised when a simulation or risk-analysis step fails at runtime."""

    def __init__(self, message: str, scenarios: int | None = None, **kwargs: Any):
        """
        Initialize Simulation Error

        Args:
            message: Error message
            scenarios: Number of scenarios that were attempted
            **kwargs: Additional details
        """
        details = {"scenarios": scenarios, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class PortfolioOptimizationError(FHSException):
    """Raised when portfolio optimization fails (e.g., no valid solution exists)."""

    def __init__(
        self,
        message: str,
        budget: float | None = None,
        constraint_type: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Portfolio Optimization Error

        Args:
            message: Error message
            budget: The budget constraint that couldn't be satisfied
            constraint_type: Type of constraint (e.g., "budget", "sprint_capacity")
            **kwargs: Additional details
        """
        details = {"budget": budget, "constraint_type": constraint_type, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class ConstraintViolationError(FHSException):
    """Raised when a domain constraint is violated."""

    def __init__(
        self,
        message: str,
        budget: float | None = None,
        constraint_type: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Constraint Violation Error

        Args:
            message: Error message
            budget: Budget value involved in the violation
            constraint_type: Type of violated constraint
            **kwargs: Additional details
        """
        details = {"budget": budget, "constraint_type": constraint_type, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class InsufficientDataError(FHSException):
    """Raised when there is insufficient data for reliable analysis."""

    def __init__(
        self,
        message: str,
        required: int | None = None,
        provided: int | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Insufficient Data Error

        Args:
            message: Error message
            required: Minimum required samples/scenarios
            provided: Number of samples/scenarios actually provided
            **kwargs: Additional details
        """
        details = {"required": required, "provided": provided, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)


class CorrelationMatrixError(FHSException):
    """Raised when a correlation matrix is invalid or not positive semi-definite."""

    def __init__(
        self,
        message: str,
        issue: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Correlation Matrix Error

        Args:
            message: Error message
            issue: Type of issue (e.g., "not_symmetric", "not_psd", "invalid_diag")
            **kwargs: Additional details
        """
        details = {"issue": issue, **kwargs}
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, details)

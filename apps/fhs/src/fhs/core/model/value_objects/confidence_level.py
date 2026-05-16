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

"""ConfidenceLevel Value Object — statistical confidence level."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConfidenceLevel(BaseModel):
    """
    Confidence Level Value Object.

    Represents a statistical confidence level (e.g., 95%, 99%).
    """

    level: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence level between 0 and 1"
    )

    model_config = {"frozen": True}  # Immutable

    @classmethod
    def from_percentage(cls, percentage: float) -> ConfidenceLevel:
        """Create from percentage (e.g., 95 -> 0.95)."""
        return cls(level=percentage / 100.0)

    def to_percentage(self) -> float:
        """Convert to percentage (e.g., 0.95 -> 95)."""
        return self.level * 100.0

    def __str__(self) -> str:
        return f"{self.to_percentage():.1f}%"

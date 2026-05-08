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

"""Budget Value Object — represents a monetary amount with currency."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Budget(BaseModel):
    """
    Budget Value Object.

    Represents a monetary amount with currency.
    Immutable and comparable.
    """

    amount: float = Field(
        ..., ge=0.0, description="Budget amount (must be non-negative)"
    )
    currency: str = Field(default="EUR", description="Currency code (ISO 4217)")

    model_config = {"frozen": True}  # Immutable

    def __add__(self, other: Budget) -> Budget:
        """Add two budgets (same currency)."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add budgets with different currencies: {self.currency} vs {other.currency}"
            )
        return Budget(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Budget) -> Budget:
        """Subtract two budgets (same currency)."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract budgets with different currencies: "
                f"{self.currency} vs {other.currency}"
            )
        return Budget(amount=self.amount - other.amount, currency=self.currency)

    def __lt__(self, other: Budget) -> bool:
        """Compare budgets."""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare budgets with different currencies: "
                f"{self.currency} vs {other.currency}"
            )
        return self.amount < other.amount

    def __le__(self, other: Budget) -> bool:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot compare budgets with different currencies: "
                f"{self.currency} vs {other.currency}"
            )
        return self.amount <= other.amount

    def __str__(self) -> str:
        return f"{self.amount:,.2f} {self.currency}"

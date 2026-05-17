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

"""Tests for Budget value object."""

from __future__ import annotations

import operator

import pytest

from fhs.core.model.value_objects.budget import Budget


class TestBudget:
    """Tests for Budget value object."""

    def test_add_same_currency(self):
        """Adding budgets with same currency works."""
        b1 = Budget(amount=1000.0, currency="EUR")
        b2 = Budget(amount=500.0, currency="EUR")
        result = b1 + b2
        assert result.amount == 1500.0
        assert result.currency == "EUR"

    def test_add_different_currency_raises(self):
        """Adding budgets with different currencies raises ValueError."""
        b1 = Budget(amount=1000.0, currency="EUR")
        b2 = Budget(amount=500.0, currency="USD")
        with pytest.raises(
            ValueError, match="Cannot add budgets with different currencies"
        ):
            b1 + b2

    def test_subtract_same_currency(self):
        """Subtracting budgets with same currency works."""
        b1 = Budget(amount=1000.0, currency="EUR")
        b2 = Budget(amount=400.0, currency="EUR")
        result = b1 - b2
        assert result.amount == 600.0
        assert result.currency == "EUR"

    def test_subtract_different_currency_raises(self):
        """Subtracting budgets with different currencies raises ValueError."""
        b1 = Budget(amount=1000.0, currency="EUR")
        b2 = Budget(amount=500.0, currency="USD")
        with pytest.raises(
            ValueError, match="Cannot subtract budgets with different currencies"
        ):
            b1 - b2

    def test_less_than_same_currency(self):
        """Comparison with same currency works."""
        b1 = Budget(amount=500.0, currency="EUR")
        b2 = Budget(amount=1000.0, currency="EUR")
        assert b1 < b2
        assert not b2 < b1

    def test_less_than_different_currency_raises(self):
        """Comparison with different currencies raises ValueError."""
        b1 = Budget(amount=500.0, currency="EUR")
        b2 = Budget(amount=1000.0, currency="USD")
        with pytest.raises(
            ValueError, match="Cannot compare budgets with different currencies"
        ):
            operator.lt(b1, b2)

    def test_less_equal_same_currency(self):
        """Less-or-equal comparison with same currency works."""
        b1 = Budget(amount=500.0, currency="EUR")
        b2 = Budget(amount=1000.0, currency="EUR")
        b3 = Budget(amount=500.0, currency="EUR")
        assert b1 <= b2
        assert b1 <= b3
        assert not b2 <= b1

    def test_less_equal_different_currency_raises(self):
        """Less-or-equal comparison with different currencies raises ValueError."""
        b1 = Budget(amount=500.0, currency="EUR")
        b2 = Budget(amount=1000.0, currency="USD")
        with pytest.raises(
            ValueError, match="Cannot compare budgets with different currencies"
        ):
            operator.le(b1, b2)

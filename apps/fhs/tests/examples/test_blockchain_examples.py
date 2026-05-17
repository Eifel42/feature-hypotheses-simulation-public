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

"""Tests for blockchain helper functions."""

import pytest

from fhs.core.model import Feature
from fhs.examples.blockchain import expected_business_value, standalone_roi


def test_expected_business_value_calculates_correctly():
    """Expected business value should multiply users x conversion x value."""
    feature = Feature(
        name="H1: Simplified UI",
        expected_users=25_000,
        conversion_rate=0.15,
        uncertainty=0.35,
        business_value_per_conversion=41.60,
        development_cost=75_000,
    )

    business_value = expected_business_value(feature)

    assert business_value == pytest.approx(156_000.0, abs=0.01)
    assert business_value == 25_000 * 0.15 * 41.60


def test_standalone_roi_positive_case():
    """ROI should be (business value - cost) / cost."""
    feature = Feature(
        name="H1: Simplified UI",
        expected_users=25_000,
        conversion_rate=0.15,
        uncertainty=0.35,
        business_value_per_conversion=41.60,
        development_cost=75_000,
    )

    roi = standalone_roi(feature)

    # Expected business value: 156,000 EUR
    # ROI = (156,000 - 75,000) / 75,000 = 1.08
    assert roi == pytest.approx(1.08, abs=0.01)
    assert roi > 1.0  # Profitable feature


def test_standalone_roi_negative_case():
    """ROI should be negative when cost exceeds business value."""
    feature = Feature(
        name="H3: Expiration Alerts",
        expected_users=8_000,
        conversion_rate=0.05,
        uncertainty=0.30,
        business_value_per_conversion=17.50,
        development_cost=20_000,
    )

    roi = standalone_roi(feature)

    # Expected business value: 7,000 EUR
    # ROI = (7,000 - 20,000) / 20,000 = -0.65
    assert roi == pytest.approx(-0.65, abs=0.01)
    assert roi < 0.0  # Loss-making feature


def test_expected_business_value_minimal_users():
    """Expected business value should be near zero if minimal users are expected."""
    feature = Feature(
        name="Test Feature",
        expected_users=1,
        conversion_rate=0.50,
        uncertainty=0.20,
        business_value_per_conversion=100.0,
        development_cost=10_000,
    )

    business_value = expected_business_value(feature)

    assert business_value == 50.0


def test_expected_business_value_zero_conversion():
    """Expected business value should be zero if conversion rate is zero."""
    feature = Feature(
        name="Test Feature",
        expected_users=10_000,
        conversion_rate=0.0,
        uncertainty=0.20,
        business_value_per_conversion=100.0,
        development_cost=10_000,
    )

    business_value = expected_business_value(feature)

    assert business_value == 0.0


def test_standalone_roi_break_even():
    """ROI should be zero when business value equals cost."""
    feature = Feature(
        name="Break-even Feature",
        expected_users=1_000,
        conversion_rate=0.10,
        uncertainty=0.20,
        business_value_per_conversion=100.0,
        development_cost=10_000,  # Same as business value
    )

    roi = standalone_roi(feature)

    assert roi == pytest.approx(0.0, abs=0.01)

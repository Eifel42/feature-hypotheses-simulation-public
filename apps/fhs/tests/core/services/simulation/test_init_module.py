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

"""Tests for simulation __init__ module lazy imports and __getattr__ error path."""

import pytest

from fhs.core.services import simulation


def test_lazy_import_feature_simulator():
    """Test lazy import of FeatureSimulator."""
    assert simulation.FeatureSimulator is not None


def test_lazy_import_portfolio_multi_year_service():
    """Test lazy import of PortfolioMultiYearService."""
    assert simulation.PortfolioMultiYearService is not None


def test_lazy_import_pnl_multi_year_service():
    """Test lazy import of PnLMultiYearService."""
    assert simulation.PnLMultiYearService is not None


def test_getattr_raises_attribute_error_for_unknown():
    """Test that __getattr__ raises AttributeError for unknown attributes."""
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = simulation.NonExistentClass

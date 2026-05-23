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

"""Tests for PortfolioPLVariants and PLVariantRow value objects."""

import pytest

from src.fhs.core.model.value_objects.portfolio_pl import (
    PLVariantRow,
    PortfolioPLVariants,
)


class TestPLVariantRow:
    def test_frozen(self):
        row = PLVariantRow(
            label="Mean (Expected)", bv=300_000, v1_net=-50_000, v2_net=80_000
        )
        try:
            row.bv = 999  # type: ignore[misc]
            assert False, "should be immutable"
        except AttributeError:
            pass
        except TypeError:
            pass

    def test_positive_v2_negative_v1(self):
        row = PLVariantRow(
            label="Mean (Expected)", bv=300_000, v1_net=-13_200, v2_net=172_000
        )
        assert row.v1_net < 0
        assert row.v2_net > 0

    def test_all_negative(self):
        row = PLVariantRow(
            label="Tail (CVaR 95%)", bv=50_000, v1_net=-163_000, v2_net=-78_000
        )
        assert row.v1_net < 0
        assert row.v2_net < 0

    def test_fields_preserved(self):
        row = PLVariantRow(
            label="Best (P95)", bv=500_000.0, v1_net=287_000.0, v2_net=372_000.0
        )
        assert row.label == "Best (P95)"
        assert row.bv == pytest.approx(500_000.0)
        assert row.v1_net == pytest.approx(287_000.0)
        assert row.v2_net == pytest.approx(372_000.0)


class TestPortfolioPLVariants:
    @staticmethod
    def _make() -> PortfolioPLVariants:
        rows = (
            PLVariantRow("Best (P95)", 500_000, 287_000, 372_000),
            PLVariantRow("Mean (Expected)", 310_000, 97_000, 182_000),
            PLVariantRow("Floor (VaR 95%)", 200_000, -13_000, 72_000),
            PLVariantRow("Tail (CVaR 95%)", 100_000, -113_000, -28_000),
        )
        return PortfolioPLVariants(
            rows=rows,
            total_investment=145_000,
            total_annual_installment=60_000,
            total_annual_opex=68_000,
        )

    def test_frozen(self):
        result = self._make()
        try:
            result.total_investment = 0  # type: ignore[misc]
            assert False, "should be immutable"
        except AttributeError:
            pass
        except TypeError:
            pass

    def test_four_rows(self):
        result = self._make()
        assert len(result.rows) == 4

    def test_row_labels(self):
        result = self._make()
        labels = [r.label for r in result.rows]
        assert "Best (P95)" in labels
        assert "Mean (Expected)" in labels
        assert "Floor (VaR 95%)" in labels
        assert "Tail (CVaR 95%)" in labels

    def test_totals_stored(self):
        result = self._make()
        assert result.total_investment == 145_000
        assert result.total_annual_installment == 60_000
        assert result.total_annual_opex == 68_000

    def test_v2_better_than_v1(self):
        """V2 net is always better than V1 net because installment < full investment."""
        result = self._make()
        for row in result.rows:
            assert row.v2_net > row.v1_net

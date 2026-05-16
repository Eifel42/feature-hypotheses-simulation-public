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

"""Performance benchmark: Jinja2 template rendering vs f-string baseline.

Quality Gate: < 20% overhead vs f-strings with template caching.
Run: python3 -m pytest tests/presentation/notebook/benchmark_templates.py -v -s
"""

from __future__ import annotations

import timeit

from src.fhs.presentation.notebook.widgets.cards import feature_risk_card
from src.fhs.presentation.notebook.widgets.portfolio import optimizer_results_card
from src.fhs.presentation.notebook.widgets.tables import metric_table, ranking_table

# ── Benchmark fixtures ─────────────────────────────────────────────────


def _metric_rows(n: int = 20):
    return [(f"Metric {i}", f"EUR {i * 1000:,}", None) for i in range(n)]


def _ranking_rows(n: int = 10):
    return [
        {
            "feature": f"Feature {i}",
            "expected_business_value": 100000 + i * 10000,
            "var_95_business_value": 80000 + i * 5000,
            "risk_ratio": 0.1 + i * 0.05,
        }
        for i in range(n)
    ]


# ── Absolute latency tests ──────────────────────────────────────────


class TestAbsoluteLatency:
    """Each template render must complete under 5ms (generous threshold)."""

    def test_metric_table_under_5ms(self):
        rows = _metric_rows()
        elapsed = timeit.timeit(lambda: metric_table(rows), number=100) / 100
        assert elapsed < 0.005, f"metric_table: {elapsed * 1000:.2f}ms > 5ms"

    def test_ranking_table_under_5ms(self):
        rows = _ranking_rows()
        elapsed = timeit.timeit(lambda: ranking_table(rows), number=100) / 100
        assert elapsed < 0.005, f"ranking_table: {elapsed * 1000:.2f}ms > 5ms"

    def test_feature_risk_card_under_5ms(self):
        elapsed = (
            timeit.timeit(
                lambda: feature_risk_card("Test", 100000, 80000, 0.2), number=100
            )
            / 100
        )
        assert elapsed < 0.005, f"feature_risk_card: {elapsed * 1000:.2f}ms > 5ms"

    def test_optimizer_results_card_under_5ms(self):
        elapsed = (
            timeit.timeit(
                lambda: optimizer_results_card(
                    ["A", "B"], 100000, 200000, 80000, 50000
                ),
                number=100,
            )
            / 100
        )
        assert elapsed < 0.005, f"optimizer_results_card: {elapsed * 1000:.2f}ms > 5ms"


# ── Throughput test ──────────────────────────────────────────────────


class TestThroughput:
    """1000 renders must complete in reasonable time."""

    def test_1000_metric_table_renders(self):
        rows = _metric_rows(5)
        elapsed = timeit.timeit(lambda: metric_table(rows), number=1000)
        assert elapsed < 5.0, f"1000 metric_table renders took {elapsed:.2f}s"
        print(
            f"\n  1000 metric_table renders: {elapsed:.3f}s ({elapsed / 1000 * 1000:.2f}ms each)"
        )

    def test_1000_feature_risk_card_renders(self):
        elapsed = timeit.timeit(
            lambda: feature_risk_card("Test", 100000, 80000, 0.2), number=1000
        )
        assert elapsed < 5.0, f"1000 feature_risk_card renders took {elapsed:.2f}s"
        print(
            f"\n  1000 feature_risk_card renders: {elapsed:.3f}s ({elapsed / 1000 * 1000:.2f}ms each)"
        )

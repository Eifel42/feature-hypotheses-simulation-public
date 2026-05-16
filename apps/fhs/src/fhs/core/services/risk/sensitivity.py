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

"""Sensitivity analysis domain service."""

from __future__ import annotations

from collections.abc import Iterable

from fhs.core.model.value_objects import (
    FeatureSensitivityResult,
    PortfolioSensitivityRow,
    SensitivityDetail,
    SensitivityDriver,
)


class SensitivityAnalysisService:
    """Build typed sensitivity outputs from feature and portfolio grids."""

    @staticmethod
    def analyze_features(
        details: Iterable[SensitivityDetail],
        drivers: Iterable[SensitivityDriver] | None = None,
    ) -> FeatureSensitivityResult:
        """Create FeatureSensitivityResult and derive drivers when omitted."""
        detail_rows = tuple(details)

        if drivers is None:
            by_feature: dict[str, list[SensitivityDetail]] = {}
            for row in detail_rows:
                by_feature.setdefault(row.feature, []).append(row)

            derived_drivers: list[SensitivityDriver] = []
            for feature, rows in by_feature.items():
                # strongest downside impact from base to high probability
                worst = min(rows, key=lambda r: r.floor_high - r.floor_base)
                derived_drivers.append(
                    SensitivityDriver(
                        feature=feature,
                        most_sensitive_driver=worst.factor,
                        floor_change_eur=worst.floor_high - worst.floor_base,
                    )
                )
            driver_rows = tuple(derived_drivers)
        else:
            driver_rows = tuple(drivers)

        return FeatureSensitivityResult(details=detail_rows, drivers=driver_rows)

    @staticmethod
    def analyze_portfolio(
        rows: Iterable[PortfolioSensitivityRow],
    ) -> list[PortfolioSensitivityRow]:
        """Return a stable, sorted portfolio sensitivity matrix."""
        return sorted(
            rows,
            key=lambda row: (row.risk_2_probability, row.risk_3_probability),
        )

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

"""Sensitivity analysis value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SensitivityDetail:
    """One row of a sensitivity analysis for one factor and feature."""

    feature: str
    factor: str
    low_probability: float
    base_probability: float
    high_probability: float
    floor_low: float
    floor_base: float
    floor_high: float
    high_vs_base_pct: float


@dataclass(frozen=True)
class SensitivityDriver:
    """Most sensitive risk driver for one feature."""

    feature: str
    most_sensitive_driver: str
    floor_change_eur: float


@dataclass(frozen=True)
class FeatureSensitivityResult:
    """Complete sensitivity analysis across features and risk factors."""

    details: tuple[SensitivityDetail, ...]
    drivers: tuple[SensitivityDriver, ...]

    def tornado_summary(self) -> tuple[TornadoRow, ...]:
        """Aggregate per-factor floor impact for tornado-style ranking."""
        grouped: dict[str, list[SensitivityDetail]] = {}
        for detail in self.details:
            grouped.setdefault(detail.factor, []).append(detail)

        rows: list[TornadoRow] = []
        for factor, factor_rows in grouped.items():
            changes = [row.floor_high - row.floor_base for row in factor_rows]
            spans = [abs(row.floor_high - row.floor_low) for row in factor_rows]
            worst_row = min(
                factor_rows, key=lambda row: row.floor_high - row.floor_base
            )
            worst_change = worst_row.floor_high - worst_row.floor_base

            rows.append(
                TornadoRow(
                    factor=factor,
                    avg_floor_change_eur=(
                        (sum(changes) / len(changes)) if changes else 0.0
                    ),
                    avg_floor_span_eur=(sum(spans) / len(spans)) if spans else 0.0,
                    worst_feature=worst_row.feature,
                    worst_floor_change_eur=worst_change,
                )
            )

        return tuple(
            sorted(rows, key=lambda row: abs(row.avg_floor_change_eur), reverse=True)
        )


@dataclass(frozen=True)
class TornadoRow:
    """One aggregated tornado line for a sensitivity factor."""

    factor: str
    avg_floor_change_eur: float
    avg_floor_span_eur: float
    worst_feature: str
    worst_floor_change_eur: float


@dataclass(frozen=True)
class PortfolioSensitivityRow:
    """One point in a portfolio sensitivity grid."""

    risk_2_probability: float
    risk_3_probability: float
    expected: float
    var_95: float
    cvar_95: float

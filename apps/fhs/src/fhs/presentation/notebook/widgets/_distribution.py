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

"""Distribution-analysis methods."""

from __future__ import annotations

from typing import Any


class _DistributionMixin:
    # Host stub for static typing; concrete implementation is provided by facade mixins.
    def sensitivity(
        self,
        _rows: list[tuple[str, ...]],
        _headers: tuple[str, ...],
        **_kwargs: Any,
    ) -> None:  # pragma: no cover - typing stub
        return None

    def negative_score_filter(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Individual var_floor Scores — ILP Candidate Filter",
    ) -> None:
        """Render per-feature var_floor scores and ILP treatment hints."""
        self.sensitivity(
            rows,
            (
                "Feature",
                "Cost",
                "BVF 95%",
                "var_floor Score (BVF95 − Cost)",
                "ILP treatment",
            ),
            title=title,
        )

    def negative_score_effect(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Negative-Score Effect: All Features vs Positive-Score Only",
    ) -> None:
        """Render candidate-set comparison for Exact vs ILP."""
        self.sensitivity(
            rows,
            (
                "Candidate set",
                "Solver",
                "Selected features",
                "#",
                "Floor (BVF 95%)",
                "Cost",
            ),
            title=title,
        )

    def runtime_scaling(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Runtime Scaling Table (var_floor)",
    ) -> None:
        """Render standardized runtime vs quality scaling rows."""
        self.sensitivity(
            rows,
            (
                "Num Features",
                "Method",
                "Budget Used",
                "Floor (BVF 95%)",
                "Runtime",
            ),
            title=title,
        )

    @staticmethod
    def beta_sample_size_effect(
        *,
        n_samples: int = 10_000,
        seed: int = 42,
        title: str = "Beta Distribution: More Data = Narrower Estimate",
    ) -> None:
        """Render standardized beta sample-size confidence chart."""
        from ..charts.distributions import plot_beta_sample_size_effect

        plot_beta_sample_size_effect(
            n_samples=n_samples,
            seed=seed,
            title=title,
        )

    @staticmethod
    def beta_vs_normal_boxplot(
        *,
        mean_rate: float = 0.08,
        uncertainty: float = 0.40,
        n_samples: int = 10_000,
        seed: int = 42,
    ) -> dict[str, float]:
        """Render beta-vs-normal comparison chart and return summary metrics."""
        from ..charts.distributions import plot_beta_vs_normal_boxplot

        _, summary = plot_beta_vs_normal_boxplot(
            mean_rate=mean_rate,
            uncertainty=uncertainty,
            n_samples=n_samples,
            seed=seed,
        )
        return summary

    @staticmethod
    def distribution_risk_metric_comparison(
        *,
        mean_rate: float = 0.08,
        uncertainty: float = 0.40,
        n_users: int = 5_000,
        business_value_per_conversion: float = 150.0,
        n_samples: int = 50_000,
        seed: int = 42,
    ) -> dict[str, float]:
        """Render distribution VaR/CVaR comparison chart and return key metrics."""
        from ..charts.distributions import plot_distribution_risk_metric_comparison

        _, summary = plot_distribution_risk_metric_comparison(
            mean_rate=mean_rate,
            uncertainty=uncertainty,
            n_users=n_users,
            business_value_per_conversion=business_value_per_conversion,
            n_samples=n_samples,
            seed=seed,
        )
        return summary

    @staticmethod
    def distribution_shape_comparison(
        *,
        mean_rate: float = 0.08,
        n_samples: int = 10_000,
        seed: int = 42,
    ) -> dict[str, float]:
        """Render three-distribution shape comparison and return summary metrics."""
        from ..charts.distributions import plot_distribution_shape_comparison

        _, summary = plot_distribution_shape_comparison(
            mean_rate=mean_rate,
            n_samples=n_samples,
            seed=seed,
        )
        return summary

    @staticmethod
    def normal_distribution_deep_dive(
        *,
        mean_rate: float = 0.08,
        high_uncertainty: float = 0.5,
        n_samples: int = 10_000,
        seed: int = 42,
    ) -> dict[str, float]:
        """Render normal clipping/uncertainty deep dive and return summary metrics."""
        from ..charts.distributions import plot_normal_distribution_deep_dive

        _, summary = plot_normal_distribution_deep_dive(
            mean_rate=mean_rate,
            high_uncertainty=high_uncertainty,
            n_samples=n_samples,
            seed=seed,
        )
        return summary

    @staticmethod
    def lognormal_distribution_deep_dive(
        *,
        normal_mean: float = 1_000.0,
        normal_std: float = 500.0,
        lognormal_scale: float = 800.0,
        lognormal_sigma: float = 0.5,
        n_samples: int = 10_000,
        seed: int = 42,
    ) -> dict[str, float]:
        """Render lognormal deep dive and return skewness summary metrics."""
        from ..charts.distributions import plot_lognormal_distribution_deep_dive

        _, summary = plot_lognormal_distribution_deep_dive(
            normal_mean=normal_mean,
            normal_std=normal_std,
            lognormal_scale=lognormal_scale,
            lognormal_sigma=lognormal_sigma,
            n_samples=n_samples,
            seed=seed,
        )
        return summary

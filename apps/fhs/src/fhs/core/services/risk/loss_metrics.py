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

"""Loss metrics domain service."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import numpy as np

from fhs.core.model.value_objects import LossMetrics, LossProfile


class LossMetricsService:
    """Build loss metrics from simulation-backed portfolio inputs."""

    @staticmethod
    def from_subset_pnl_function(
        *,
        selected: Iterable[str],
        delivery_gates: Mapping[str, np.ndarray],
        development_cost_by_feature: Mapping[str, float],
        pnl_function: Callable[[], np.ndarray],
        loss_profile_function: Callable[[np.ndarray, float], LossProfile],
        confidence: float = 0.95,
    ) -> LossMetrics:
        """Create typed LossMetrics from delivery gates and full-risk P&L.

        The `pnl_function` must return the year-1 full-risk P&L distribution.
        The `loss_profile_function` calculates a LossProfile from (pnl, confidence).
        """
        if not 0.0 < confidence < 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        selected_tuple = tuple(selected)
        if not selected_tuple:
            empty = loss_profile_function(np.array([], dtype=float), confidence)
            return LossMetrics(
                year1=empty,
                catastrophe_threshold=0.0,
                catastrophe_probability=0.0,
                cvar_loss=empty.loss_cvar,
                investment=0.0,
            )

        pnl_full = np.asarray(pnl_function(), dtype=float)
        profile = loss_profile_function(pnl_full, confidence)

        all_fail = np.ones(len(pnl_full), dtype=bool)
        for name in selected_tuple:
            gate = delivery_gates.get(name)
            if gate is None:
                raise KeyError(f"Missing delivery gate scenarios for feature '{name}'.")
            gate_arr = np.asarray(gate, dtype=bool)
            if len(gate_arr) != len(pnl_full):
                raise ValueError(
                    f"Delivery gate length mismatch for feature '{name}': "
                    f"{len(gate_arr)} != {len(pnl_full)}."
                )
            all_fail &= ~gate_arr

        investment = float(
            sum(float(development_cost_by_feature[name]) for name in selected_tuple)
        )

        return LossMetrics(
            year1=profile,
            catastrophe_threshold=investment,
            catastrophe_probability=float(np.mean(all_fail)),
            cvar_loss=profile.loss_cvar,
            investment=investment,
        )

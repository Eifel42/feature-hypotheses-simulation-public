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

"""Shared helpers for Monte Carlo simulation (§10.2 DDD Refactoring).

Eliminates 4 duplicated code paths across simulate(), simulate_bounded(),
simulate_correlated(), and simulate_copula().
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from fhs.core.typing_utils import NDArrayFloat, to_float_array

logger = logging.getLogger("fhs.monte_carlo")


# noinspection PyTypeHintsInspection
def apply_bounds(array: np.ndarray | Any, lo: float, hi: float) -> NDArrayFloat:
    """Clip array values to [lo, hi] and return a float64 ndarray.

    This helper narrows dynamic inputs (lists, object arrays) to a
    NumPy float64 array which reduces mypy complaints at numeric call sites.
    """
    arr = to_float_array(array)
    return np.clip(arr, lo, hi)


# noinspection PyTypeHintsInspection
def apply_acceptance_model(
    rates: np.ndarray | Any,
    feature: Any,
    rng: np.random.Generator,
) -> NDArrayFloat:
    """Convert conversion rates to absolute counts using the feature's acceptance model.

    Args:
        rates: Simulated conversion rates (clipped to [0, 1])
        feature: Feature object
        rng: Random number generator

    Returns:
        Absolute conversion counts
    """
    arr = to_float_array(rates)
    if getattr(feature, "acceptance_model", "") == "binomial":
        # rng.binomial returns integer counts; convert to float for downstream
        # numeric calculations and to keep a consistent NDArrayFloat return type.
        return arr.astype(float) * 0.0 + rng.binomial(int(feature.expected_users), arr)
    return arr * float(feature.expected_users)


def auto_select_distribution(
    distribution: str,
    uncertainty: float,
    base_value: float,
) -> str:
    """Auto-switch distribution based on uncertainty level.

    When uncertainty >= 0.3 and base distribution is normal, switch to
    lognormal to avoid clipping bias at the [0, 1] bounds.

    The switch is logged at WARNING level so callers are notified when
    the requested distribution is silently overridden.
    """
    if distribution == "normal" and uncertainty >= 0.3 and base_value > 0:
        logger.warning(
            "Distribution auto-switched: 'normal' → 'lognormal' "
            "(uncertainty=%.2f >= 0.3). "
            "Normal distribution would introduce >1%% clipping bias at high uncertainty. "
            "Set distribution='lognormal' explicitly to suppress this message.",
            uncertainty,
        )
        return "lognormal"
    return distribution

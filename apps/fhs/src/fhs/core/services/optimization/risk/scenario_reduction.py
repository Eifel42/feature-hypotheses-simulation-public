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

"""Scenario reduction utility for risk-aware optimization."""

from __future__ import annotations

import numpy as np


def reduce_scenarios(
    feature_scenarios: dict[str, np.ndarray],
    n_reduced: int = 300,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Reduce scenario matrix via MiniBatch k-means clustering.

    Args:
        feature_scenarios: Mapping ``feature_name -> scenario_vector``.
        n_reduced: Number of reduced representative scenarios.
        seed: RNG seed for deterministic cluster initialization.

    Returns:
        Tuple ``(reduced_matrix, weights)`` where:
        - ``reduced_matrix`` has shape ``(n_reduced, J)``
        - ``weights`` has shape ``(n_reduced,)`` and sums to 1
    """
    if not feature_scenarios:
        raise ValueError("feature_scenarios must not be empty")
    if n_reduced < 1:
        raise ValueError(
            f"n_reduced must be >= 1, got {n_reduced}"
        )  # pragma: no cover - defensive

    try:
        from sklearn.cluster import MiniBatchKMeans
    except ImportError as exc:
        raise ImportError(
            "Scenario reduction requires scikit-learn. "
            "Install it with `pip install scikit-learn`."
        ) from exc

    names = list(feature_scenarios.keys())
    arrays = [
        np.asarray(feature_scenarios[name], dtype=float).reshape(-1) for name in names
    ]

    first_len = len(arrays[0])
    if first_len == 0:
        raise ValueError(
            "scenario arrays must not be empty"
        )  # pragma: no cover - defensive

    if any(len(arr) != first_len for arr in arrays):
        raise ValueError(
            "all feature scenario arrays must have the same length"
        )  # pragma: no cover - defensive
    if n_reduced > first_len:
        raise ValueError(  # pragma: no cover - defensive
            f"n_reduced ({n_reduced}) must not exceed number of scenarios ({first_len})"
        )

    matrix = np.column_stack(arrays)  # (N, J)
    if not np.isfinite(matrix).all():
        raise ValueError(
            "feature_scenarios contains non-finite values"
        )  # pragma: no cover - defensive

    # Scale to avoid numerical issues in k-means for high-magnitude business value data.
    col_mean = np.mean(matrix, axis=0)
    col_std = np.std(matrix, axis=0)
    col_std = np.where(col_std > 1e-12, col_std, 1.0)
    scaled = (matrix - col_mean) / col_std

    kmeans = MiniBatchKMeans(
        n_clusters=n_reduced,
        random_state=seed,
        n_init=10,
    )
    # sklearn can emit benign floating warnings in some BLAS backends.
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        labels = kmeans.fit_predict(scaled)

    reduced_matrix = np.asarray(kmeans.cluster_centers_, dtype=float)
    reduced_matrix = reduced_matrix * col_std + col_mean
    counts = np.bincount(labels, minlength=n_reduced).astype(float)
    weights = counts / float(first_len)

    # Canonicalize order to avoid label-permutation noise in deterministic tests.
    # reduced_matrix.shape[1] is always > 0 because empty feature_scenarios is
    # rejected earlier in _validate_inputs, so a sort-key column always exists.
    keys = tuple(
        reduced_matrix[:, idx] for idx in reversed(range(reduced_matrix.shape[1]))
    )
    order = np.lexsort(keys)
    reduced_matrix = reduced_matrix[order]
    weights = weights[order]

    return reduced_matrix, weights

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

"""
Correlation Builder

Extracted from portfolio.py (§3.2 DDD Refactoring).
Builds correlation matrices from dependency clusters using explicit config.
"""

import logging

import numpy as np

from ...model import Feature

logger = logging.getLogger("fhs.correlation_builder")


# Default correlation values for dependency clusters
DEPENDENCY_CORRELATION_DEFAULTS = {
    "shared_team": 0.5,
    "technical_dependency": 0.8,
    "same_user_segment": 0.3,
    "independent": 0.0,
}


def _cluster_correlation(cluster: str) -> float:
    cluster_lower = cluster.lower()
    if "team" in cluster_lower:
        return DEPENDENCY_CORRELATION_DEFAULTS["shared_team"]
    if "api" in cluster_lower or "dependency" in cluster_lower:
        return DEPENDENCY_CORRELATION_DEFAULTS["technical_dependency"]
    if "user" in cluster_lower or "segment" in cluster_lower:
        return DEPENDENCY_CORRELATION_DEFAULTS["same_user_segment"]
    return DEPENDENCY_CORRELATION_DEFAULTS["shared_team"]


def _apply_cluster_correlations(
    corr_matrix: np.ndarray, indices: list[int], correlation: float
) -> None:
    for i in indices:
        for j in indices:
            if i != j:
                corr_matrix[i, j] = correlation


def build_correlation_matrix_from_clusters(
    features: list[Feature],
) -> np.ndarray:
    """
    Build correlation matrix from dependency clusters.

    Features in the same dependency cluster are assumed to have correlated
    delivery risk. This avoids asking teams to estimate correlation numbers
    directly.

    Default correlation values:
    - Shared Team: ρ = 0.5
    - Technical Dependency: ρ = 0.8
    - Same User Segment: ρ = 0.3
    - Independent (no cluster): ρ = 0.0

    Args:
        features: List of Feature objects with dependency_cluster attributes

    Returns:
        np.ndarray: Correlation matrix (n_features × n_features)
    """
    n = len(features)
    corr_matrix = np.eye(n)

    clusters: dict[str, list[int]] = {}
    for i, feature in enumerate(features):
        if feature.dependency_cluster:
            cluster = feature.dependency_cluster
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(i)

    for cluster, indices in clusters.items():
        _apply_cluster_correlations(corr_matrix, indices, _cluster_correlation(cluster))

    return corr_matrix

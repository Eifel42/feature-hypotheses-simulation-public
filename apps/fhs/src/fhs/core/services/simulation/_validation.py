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
Shared validation and parameter helpers for Monte Carlo routines.
"""

from __future__ import annotations

import logging
import math

import numpy as np
from scipy import linalg

from fhs.core.model import DEFAULT_CONFIG
from fhs.core.model.exceptions import CorrelationMatrixError, ValidationError
from fhs.core.model.value_objects import BetaParameters

logger = logging.getLogger("fhs.monte_carlo")


def validate_scenarios(scenarios: int) -> None:
    if scenarios < DEFAULT_CONFIG.MIN_SCENARIOS:
        raise ValidationError(
            f"Minimum {DEFAULT_CONFIG.MIN_SCENARIOS} scenarios required for reliable results. "
            f"Got {scenarios}.",
            field="scenarios",
            value=scenarios,
        )


def validate_uncertainty(uncertainty: float) -> None:
    if uncertainty < 0 or uncertainty > 1:
        raise ValidationError(
            f"Uncertainty must be between 0 and 1. Got {uncertainty}.",
            field="uncertainty",
            value=uncertainty,
        )


def beta_params_from_mean_uncertainty(
    mean: float, uncertainty: float
) -> tuple[float, float]:
    params = BetaParameters.from_mean_uncertainty(
        mean=mean,
        uncertainty=uncertainty,
    )
    return params.alpha, params.beta


def lognorm_params_from_mean_uncertainty(
    mean: float, uncertainty: float
) -> tuple[float, float]:
    if mean <= 0:
        raise ValidationError(
            "Log-Normal distribution requires base_value > 0.",
            field="mean",
            value=mean,
        )
    sigma_log = uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
    mu_log = math.log(mean) - 0.5 * sigma_log**2
    return mu_log, sigma_log


def ensure_psd(
    corr: np.ndarray,
    repair: bool = False,
    threshold: float = 1e-8,
) -> np.ndarray:
    """
    Ensure a correlation matrix is positive semi-definite.

    Args:
        corr: Correlation matrix
        repair: Whether to project to nearest PSD if not PSD
        threshold: Eigenvalue threshold for projection

    Returns:
        PSD matrix (possibly repaired)

    Raises:
        CorrelationMatrixError if matrix is not PSD and repair=False or repair fails.
    """
    try:
        np.linalg.cholesky(corr)
        return corr
    except np.linalg.LinAlgError as exc:
        if not repair:
            raise CorrelationMatrixError(
                "Correlation matrix is not positive semi-definite. "
                "Enable repair to project to nearest PSD.",
                issue="not_psd",
            ) from exc

        # Project to PSD via eigendecomposition and then normalize back to
        # a valid correlation matrix with unit diagonal.
        corr_sym = (corr + corr.T) / 2.0
        eigvals, eigvecs = linalg.eigh(corr_sym)
        n_negative = int(np.sum(eigvals < 0))
        min_eigval = float(np.min(eigvals))
        logger.warning(
            "Correlation matrix is not PSD: %d negative eigenvalue(s), "
            "min eigenvalue=%.6g. Projecting to nearest PSD matrix "
            "(threshold=%.2g). Consider supplying a valid correlation matrix.",
            n_negative,
            min_eigval,
            threshold,
        )
        eigvals_clipped = np.clip(eigvals, threshold, None)
        psd_matrix = eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T

        diag = np.sqrt(np.clip(np.diag(psd_matrix), threshold, None))
        corr_repaired = psd_matrix / np.outer(diag, diag)
        corr_repaired = (corr_repaired + corr_repaired.T) / 2.0
        np.fill_diagonal(corr_repaired, 1.0)

        try:
            np.linalg.cholesky(corr_repaired)
        except np.linalg.LinAlgError as exc:  # pragma: no cover - defensive
            raise CorrelationMatrixError(
                "Correlation matrix could not be repaired to PSD.",
                issue="not_psd",
            ) from exc
        return np.asarray(corr_repaired, dtype=float)

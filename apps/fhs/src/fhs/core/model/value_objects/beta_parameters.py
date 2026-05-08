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

"""Beta distribution parameter value object."""

from __future__ import annotations

from dataclasses import dataclass

from fhs.core.model.exceptions import ValidationError


@dataclass(frozen=True)
class BetaParameters:
    """Shape parameters for a beta distribution."""

    alpha: float
    beta: float

    @classmethod
    def from_mean_uncertainty(
        cls,
        mean: float,
        uncertainty: float,
        sigma_multiplier: float = 3.0,
    ) -> BetaParameters:
        """Build beta shape parameters from mean and relative uncertainty."""
        if not 0 < mean < 1:
            raise ValidationError(
                "Beta distribution requires 0 < mean < 1.",
                field="mean",
                value=mean,
            )

        if sigma_multiplier <= 0:
            raise ValidationError(
                "sigma_multiplier must be positive.",
                field="sigma_multiplier",
                value=sigma_multiplier,
            )

        std = mean * uncertainty / sigma_multiplier
        var = std**2
        max_var = mean * (1 - mean)
        var = min(var, 0.999 * max_var)

        k = mean * (1 - mean) / var - 1
        alpha = max(mean * k, 1e-6)
        beta_param = max((1 - mean) * k, 1e-6)
        return cls(alpha=alpha, beta=beta_param)

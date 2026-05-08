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

"""Lightweight typing and runtime helpers shared across core modules.

This module provides NumPy typing aliases and safe conversion helpers that
are intentionally minimal and have runtime checks to narrow types for mypy.

It lives at ``fhs.core`` level (not under ``fhs.core.services`` or
``fhs.core.model``) so that domain services can import it without
triggering domain_service→infrastructure layer-boundary violations.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

NDArrayFloat = NDArray[np.float64]


def to_float_array(x: Any) -> NDArrayFloat:
    """Convert input to a NumPy float64 array (non-destructive).

    This narrows dynamic 'object' types for mypy and ensures numeric dtype
    for downstream math (np.mean, np.where, etc.).
    """
    arr = np.asarray(x)
    if arr.dtype == object:
        # attempt to coerce to float; raises if impossible which surfaces at runtime
        arr = arr.astype(float)
    return arr.astype(np.float64)

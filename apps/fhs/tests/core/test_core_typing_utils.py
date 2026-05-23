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

"""Tests for core typing utilities."""

from __future__ import annotations

import numpy as np

from fhs.core.typing_utils import to_float_array


def test_to_float_array_from_list():
    """Convert list to float array."""
    result = to_float_array([1, 2, 3])
    assert result.dtype == np.float64
    np.testing.assert_array_equal(result, [1.0, 2.0, 3.0])


def test_to_float_array_from_numpy_int():
    """Convert numpy int array to float."""
    result = to_float_array(np.array([1, 2, 3]))
    assert result.dtype == np.float64


def test_to_float_array_from_string_list():
    """Convert list of numeric strings (object dtype) to float."""
    # This hits the arr.dtype == object branch at line 44
    result = to_float_array(["1.0", "2.5", "3.7"])
    assert result.dtype == np.float64
    np.testing.assert_array_almost_equal(result, [1.0, 2.5, 3.7])


def test_to_float_array_already_float():
    """Already float64 array stays float64."""
    arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    result = to_float_array(arr)
    assert result.dtype == np.float64

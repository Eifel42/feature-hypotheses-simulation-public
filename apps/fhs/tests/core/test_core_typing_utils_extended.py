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

"""Extended tests for core typing utilities - covering object dtype branch."""

import numpy as np
import pytest

from fhs.core.typing_utils import to_float_array


def test_to_float_array_object_dtype_non_numeric_raises():
    """Object dtype with non-numeric values should raise during astype(float)."""
    # Create an object array with non-numeric content
    arr = np.array(["abc", "def", "ghi"], dtype=object)
    with pytest.raises(ValueError):
        to_float_array(arr)

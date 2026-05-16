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

"""Backward-compatible notebook style re-exports.

Use `fhs.presentation.notebook` in new code.
"""

from fhs.presentation.notebook import (
    COLORS,
    FIG,
    info_box,
    kpi_card,
    palette,
    setup_style,
    show,
)

__all__ = [
    "COLORS",
    "FIG",
    "info_box",
    "kpi_card",
    "palette",
    "setup_style",
    "show",
]

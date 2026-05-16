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

"""Loss profile and loss metrics value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LossProfile:
    """Financial loss profile at a given confidence level."""

    confidence: float
    pnl_expected: float
    pnl_var: float
    pnl_cvar: float
    loss_expected: float
    loss_var: float
    loss_cvar: float
    worst_case_loss: float


@dataclass(frozen=True)
class LossMetrics:
    """Structured loss metrics for a portfolio."""

    year1: LossProfile
    catastrophe_threshold: float
    catastrophe_probability: float
    cvar_loss: float
    investment: float

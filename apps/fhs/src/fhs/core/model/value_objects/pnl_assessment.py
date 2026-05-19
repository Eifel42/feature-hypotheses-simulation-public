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

"""P&L assessment value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PnLAssessment:
    """Break-even assessment based on final P&L risk layer."""

    investment_eur: float
    expected_business_value_eur: float
    var_95_business_value_eur: float
    cvar_95_business_value_eur: float
    net_expected_eur: float
    net_var_95_eur: float
    break_even_expected: bool
    break_even_var_95: bool

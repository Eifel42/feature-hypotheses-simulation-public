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

"""Table widget submodules with backward-compatible re-exports."""

from .comparison import comparison_table, ranking_table
from .decision import backlog_table, sensitivity_table
from .metrics import metric_table
from .risk import risk_contribution_table, stress_test_table
from .samples import sample_table

__all__ = [
    "backlog_table",
    "comparison_table",
    "metric_table",
    "ranking_table",
    "risk_contribution_table",
    "sample_table",
    "sensitivity_table",
    "stress_test_table",
]

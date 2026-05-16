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

"""Monte Carlo simulation package.

Re-exports MonteCarloEngine for backward compatibility.
"""

from .correlation import (
    CholeskyCorrelator,
    CopulaCorrelator,
    CorrelationFactory,
    CorrelationStrategy,
)
from .distributions import (
    BetaDistribution,
    DistributionFactory,
    DistributionStrategy,
    LognormalDistribution,
    NormalDistribution,
    TruncatedNormalDistribution,
    UniformDistribution,
)
from .engine import MonteCarloEngine

__all__ = [
    "BetaDistribution",
    "CholeskyCorrelator",
    "CopulaCorrelator",
    "CorrelationFactory",
    "CorrelationStrategy",
    "DistributionFactory",
    "DistributionStrategy",
    "LognormalDistribution",
    "MonteCarloEngine",
    "NormalDistribution",
    "TruncatedNormalDistribution",
    "UniformDistribution",
]

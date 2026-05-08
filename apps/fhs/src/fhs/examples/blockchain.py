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
Eifel42 Agra Corp. — Blockchain Agriculture Case Study

Helper functions for blockchain scenario calculations.
Configuration is now centralized in: notebooks/config/blockchain.yaml

Use load_scenario() from fhs.notebook to load the scenario configuration.
"""

from fhs.core.model import Feature


def expected_business_value(feature: Feature) -> float:
    """
    Calculate expected business value (users × conversion × value per conversion).

    Args:
        feature: Feature object with expected_users, conversion_rate,
                 and business_value_per_conversion

    Returns:
        Expected annual business value in EUR

    Example:
        >>> from fhs import Feature
        >>> f = Feature(
        ...     name="H1",
        ...     expected_users=25000,
        ...     conversion_rate=0.15,
        ...     uncertainty=0.35,
        ...     business_value_per_conversion=41.60,
        ...     development_cost=75000
        ... )
        >>> expected_business_value(f)
        156000.0
    """
    return (
        feature.expected_users
        * feature.conversion_rate
        * feature.business_value_per_conversion
    )


def standalone_roi(feature: Feature) -> float:
    """
    Calculate standalone ROI as a fraction.

    Args:
        feature: Feature object with business value and cost attributes

    Returns:
        ROI as fraction (e.g., 1.08 = +108% ROI)

    Example:
        >>> f = Feature(
        ...     name="H1",
        ...     expected_users=25000,
        ...     conversion_rate=0.15,
        ...     uncertainty=0.35,
        ...     business_value_per_conversion=41.60,
        ...     development_cost=75000
        ... )
        >>> roi = standalone_roi(f)
        >>> roi  # doctest: +ELLIPSIS
        1.08
    """
    bv = expected_business_value(feature)
    return (bv - feature.development_cost) / feature.development_cost

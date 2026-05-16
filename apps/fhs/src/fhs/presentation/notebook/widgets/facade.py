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

"""Display facade for notebook widgets."""

from __future__ import annotations

from typing import Any

from ._capital_budgeting import _CapitalBudgetingMixin
from ._delivery import _DeliveryMixin
from ._distribution import _DistributionMixin
from ._portfolio import _PortfolioMixin
from ._primitives import _PrimitivesMixin
from ._risk import _RiskMixin
from .tables import sensitivity_table


class FHSDisplay(
    _PrimitivesMixin,
    _CapitalBudgetingMixin,
    _RiskMixin,
    _PortfolioMixin,
    _DistributionMixin,
    _DeliveryMixin,
):
    """Convenience wrapper that eliminates display(HTML(...)) boilerplate."""

    # Keep this method on the facade module so tests can monkeypatch
    # facade.sensitivity_table without reaching into mixin internals.
    def sensitivity(
        self,
        rows: list[tuple[Any, ...]],
        headers: tuple[str, ...],
        **kwargs: Any,
    ) -> None:
        self(sensitivity_table(rows, headers, **kwargs))

    def sensitivity_html(
        self,
        rows: list[tuple[Any, ...]],
        headers: tuple[str, ...],
        **kwargs: Any,
    ) -> str:
        """Return a sensitivity table as an HTML string without displaying."""
        return sensitivity_table(rows, headers, **kwargs)


show = FHSDisplay()

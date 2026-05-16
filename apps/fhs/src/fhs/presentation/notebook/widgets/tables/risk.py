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

"""Risk-centric table widgets."""

from __future__ import annotations

from ...template_engine import render


def risk_contribution_table(
    rows: list[tuple[str, float, float, float, float, float]],
) -> str:
    """Return feature-level risk contribution table."""
    return render("tables/risk_contribution_table.html.j2", rows=rows)


def stress_test_table(
    scenarios: list[dict], baseline: float, *, title: str = "Stress Test Results"
) -> str:
    """Display stress test scenarios with baseline comparison."""
    return render(
        "tables/stress_test_table.html.j2",
        scenarios=scenarios,
        baseline=baseline,
        title=title,
    )

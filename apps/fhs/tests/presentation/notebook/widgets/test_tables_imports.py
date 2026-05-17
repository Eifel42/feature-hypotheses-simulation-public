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

from __future__ import annotations


def test_widget_package_reexport_import_path() -> None:
    from src.fhs.presentation.notebook.widgets import metric_table

    assert callable(metric_table)


def test_tables_module_import_path() -> None:
    from src.fhs.presentation.notebook.widgets.tables import metric_table, sample_table

    assert callable(metric_table)
    assert callable(sample_table)

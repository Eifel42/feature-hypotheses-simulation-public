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

import matplotlib.pyplot as plt
import numpy as np
import pytest

from src.fhs.presentation.notebook.charts import plot_correlation_heatmap


def test_plot_correlation_heatmap_returns_figure() -> None:
    features = ["Feature A", "Feature B", "Feature C"]
    matrix = np.array([[1.0, 0.5, 0.2], [0.5, 1.0, 0.7], [0.2, 0.7, 1.0]])
    fig = plot_correlation_heatmap(features, matrix)
    assert fig is not None
    assert len(fig.axes) == 2
    plt.close(fig)


def test_plot_correlation_heatmap_custom_figsize() -> None:
    fig = plot_correlation_heatmap(["A", "B"], np.eye(2), figsize=(8.0, 6.0))
    width, height = fig.get_size_inches()
    assert width == pytest.approx(8.0)
    assert height == pytest.approx(6.0)
    plt.close(fig)

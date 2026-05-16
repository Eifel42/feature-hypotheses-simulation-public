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

"""Correlation heatmap chart for feature dependencies."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from ..styling import FIG
from ._helpers import _apply_axis_style, _show_fig


def plot_correlation_heatmap(
    features: list[str],
    correlation_matrix: np.ndarray,
    *,
    title: str = "Feature Correlation Heatmap",
    figsize: tuple[float, float] | None = None,
) -> Figure:
    """Plot a feature-correlation heatmap with unified notebook styling."""
    fig, ax = plt.subplots(figsize=figsize or FIG.single)

    image = ax.imshow(correlation_matrix, cmap="RdBu", vmin=-1.0, vmax=1.0)
    ax.set_xticks(range(len(features)))
    ax.set_yticks(range(len(features)))
    ax.set_xticklabels(features, rotation=45, ha="right")
    ax.set_yticklabels(features)
    ax.set_title(title)

    _apply_axis_style(ax, grid_axis="both")
    fig.colorbar(image, ax=ax, label="Correlation")
    fig.tight_layout()
    _show_fig(fig)

    return fig

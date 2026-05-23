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

"""Chart styling configuration — colour palette, figure sizes, and matplotlib defaults.

This module is part of the Presentation Layer and contains all styling constants
used by Jupyter notebooks and visualisation components.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

# ── Colour palette ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Colors:
    """Semantic colour tokens for charts and HTML widgets.

    All text colours meet WCAG 2.1 AA contrast ratio (≥ 4.5 : 1) on white.
    Inspired by Google Material Design data-visualisation palette.
    """

    primary: str = "#1A73E8"
    secondary: str = "#137333"
    accent: str = "#9334E6"
    danger: str = "#C5221F"
    warning: str = "#B06000"
    info: str = "#1A73E8"
    tertiary: str = "#00796B"
    neutral: str = "#3C4043"
    subtle: str = "#5F6368"
    muted: str = "#888888"
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    success: str = "#137333"
    border: str = "#dadce0"
    grid: str = "#e8eaed"
    # Vivid badge tokens — higher contrast for IRR pills and cashflow text
    success_vivid: str = "#0d652d"
    danger_vivid: str = "#a50e0e"
    success_surface: str = "#e6f4ea"
    danger_surface: str = "#fce8e6"
    success_border: str = "#34a853"
    danger_border: str = "#ea4335"
    heatmap_label_text: str = "#202124"
    heatmap_loss_deep: str = "#B3261E"
    heatmap_loss_mid: str = "#E46962"
    heatmap_loss_soft: str = "#F2B8B5"
    heatmap_break_even: str = "#F8F9FA"
    heatmap_profit_soft: str = "#DDEDE3"
    heatmap_profit_mid: str = "#78A783"
    heatmap_profit_deep: str = "#0B8043"


LIGHT_PALETTE = _Colors()

DARK_PALETTE = _Colors(
    primary="#64B5F6",
    secondary="#4DD0E1",
    accent="#BA68C8",
    danger="#EF5350",
    warning="#FFA726",
    info="#64B5F6",
    tertiary="#4DB6AC",
    neutral="#E0E0E0",
    subtle="#9AA0A6",
    muted="#BDBDBD",
    background="#1E1E1E",
    surface="#2D2D2D",
    success="#66BB6A",
    border="#404040",
    grid="#363636",
    success_vivid="#81C995",
    danger_vivid="#F28B82",
    success_surface="#1E3A2A",
    danger_surface="#3A1E1E",
    success_border="#66BB6A",
    danger_border="#EF5350",
    heatmap_label_text="#202124",
    heatmap_loss_deep="#B3261E",
    heatmap_loss_mid="#E46962",
    heatmap_loss_soft="#F2B8B5",
    heatmap_break_even="#F8F9FA",
    heatmap_profit_soft="#DDEDE3",
    heatmap_profit_mid="#78A783",
    heatmap_profit_deep="#0B8043",
)

# ── Named gradient for risk heatmap ────────────────────────────────────────
# Gradient from deep loss (red) through break-even (amber) to profit (green).
# Stored here so chart modules avoid hardcoded hex literals.
RISK_HEATMAP_GRADIENT: tuple[str, ...] = (
    "#C62828",
    "#EF5350",
    "#FFECB3",
    "#66BB6A",
    "#2E7D32",
)


class ThemeContext:
    """Manage active palette for light/dark notebook themes."""

    def __init__(self) -> None:
        self._theme: Literal["light", "dark"] = "light"

    @property
    def colors(self) -> _Colors:
        return DARK_PALETTE if self._theme == "dark" else LIGHT_PALETTE

    def set_theme(self, theme_name: Literal["light", "dark"]) -> None:
        self._theme = theme_name

    def __getattr__(self, name: str) -> _Colors:
        if name == "COLORS":
            return self.colors
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")


theme = ThemeContext()


class _ColorsProxy:
    """Proxy forwarding color access to the active theme palette."""

    def __getattr__(self, name: str) -> str:
        return cast(str, getattr(theme.colors, name))


COLORS = _ColorsProxy()


class _PaletteProxy(Mapping[str, str]):
    """Mapping-style palette for legacy bracket access (palette["primary"])."""

    _keys = (
        "primary",
        "secondary",
        "accent",
        "danger",
        "warning",
        "info",
        "tertiary",
        "neutral",
        "subtle",
        "muted",
        "background",
        "surface",
        "success",
        "border",
        "grid",
        "success_vivid",
        "danger_vivid",
        "success_surface",
        "danger_surface",
        "success_border",
        "danger_border",
        "heatmap_label_text",
        "heatmap_loss_deep",
        "heatmap_loss_mid",
        "heatmap_loss_soft",
        "heatmap_break_even",
        "heatmap_profit_soft",
        "heatmap_profit_mid",
        "heatmap_profit_deep",
    )

    def __getitem__(self, key: str) -> str:
        if key not in self._keys:
            raise KeyError(key)
        return cast(str, getattr(theme.colors, key))

    def __iter__(self) -> Iterator[str]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)


palette: Mapping[str, str] = _PaletteProxy()


# ── Figure sizing constants ────────────────────────────────────────────────


@dataclass(frozen=True)
class _FigSizes:
    """Standard figure sizes for consistent chart layout."""

    wide: tuple[float, float] = (15.5, 5.0)  # Three-panel row
    medium: tuple[float, float] = (13.5, 5.4)  # Two-panel row
    single: tuple[float, float] = (10.8, 5.4)  # Single chart
    small: tuple[float, float] = (10.2, 4.4)  # Compact single chart
    tall: tuple[float, float] = (10.8, 6.2)  # Taller single chart


FIG = _FigSizes()


# ── Chart defaults ─────────────────────────────────────────────────────────

HIST_BINS = 50
HIST_ALPHA = 0.55
HIST_EDGE_COLOR = LIGHT_PALETTE.background
HIST_EDGE_WIDTH = 0.2


# ── rcParams ───────────────────────────────────────────────────────────────


def _rc_params() -> dict[str, Any]:
    """Build matplotlib rcParams from the active theme."""
    return {
        "figure.facecolor": COLORS.background,
        "axes.facecolor": COLORS.background,
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": 0.22,
        "grid.color": COLORS.grid,
        "font.family": ["DejaVu Sans", "sans-serif"],
        "font.size": 12,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "axes.titlepad": 16,
        "text.color": COLORS.neutral,
        "axes.labelcolor": COLORS.neutral,
        "axes.labelsize": 12,
        "xtick.color": COLORS.neutral,
        "ytick.color": COLORS.neutral,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "figure.dpi": 110,
        "axes.linewidth": 0.9,
        "axes.edgecolor": COLORS.border,
        "grid.linestyle": "-",
        "grid.linewidth": 0.8,
        "legend.frameon": True,
        "legend.fancybox": True,
        "legend.framealpha": 0.96,
        "legend.borderaxespad": 0.8,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "axes.unicode_minus": False,
    }


def _detect_jupyter_theme() -> str:
    """Heuristically detect the active JupyterLab theme.

    Returns ``"dark"`` when JupyterLab's dark theme is active (detected via
    the ``body.jp-mod-dark`` CSS class injected by JupyterLab).
    Falls back to ``"light"`` when detection is unavailable.

    Returns
    -------
    str
        ``"dark"`` or ``"light"``
    """
    try:
        ipython_mod = importlib.import_module("IPython")
        get_ipython_fn = getattr(ipython_mod, "get_ipython", None)
        if not callable(get_ipython_fn):
            return "light"
        ip = get_ipython_fn()
        if ip is None:
            return "light"

        # JupyterLab ≥ 4 exposes theme info via the kernel's comm system.
        # A reliable fallback is to inspect `jupyter_server` metadata, but the
        # most portable approach is to check for the `jp-mod-dark` CSS class
        # present on the body element.  We run a tiny snippet of JavaScript
        # and capture the result synchronously.
        run_cell_magic = getattr(ip, "run_cell_magic", None)
        if not callable(run_cell_magic):
            return "light"
        run_cell_magic(
            "javascript",
            "",
            "if (document.body.classList.contains('jp-mod-dark')) { "
            "IPython.notebook.kernel.execute('__fhs_theme__=\"dark\"'); } "
            "else { "
            "IPython.notebook.kernel.execute('__fhs_theme__=\"light\"'); }",
        )
        # Read the variable set by the JS snippet (may not be set yet)
        ns = getattr(ip, "user_ns", None)
        if not isinstance(ns, dict):
            return "light"
        detected = ns.get("__fhs_theme__", "light")
        ns.pop("__fhs_theme__", None)
        return str(detected) if detected in ("light", "dark") else "light"
    except (AttributeError, KeyError, TypeError):  # pragma: no cover
        return "light"


def setup_style(
    style: str = "seaborn-v0_8-whitegrid",
    color_theme: str | None = None,
) -> None:
    """Apply the unified FHS chart style.

    Call this once in the first code cell of every notebook.

    Parameters
    ----------
    style:
        Matplotlib style name.  Defaults to ``"seaborn-v0_8-whitegrid"``.
    color_theme:
        ``"light"`` (default), ``"dark"``, or ``"auto"`` to detect the active
        JupyterLab theme automatically.  Switching themes changes the active
        colour palette for all subsequent chart calls in the session.

    Examples
    --------
    >>> setup_style()                      # light mode (default)
    >>> setup_style(color_theme="dark")    # dark mode
    >>> setup_style(color_theme="auto")    # detect JupyterLab theme
    """
    import matplotlib.pyplot as plt

    resolved = color_theme
    if resolved == "auto":
        resolved = _detect_jupyter_theme()
    if resolved in ("light", "dark"):
        theme.set_theme(resolved)  # type: ignore[arg-type]

    try:
        plt.style.use(style)
    except OSError:
        plt.style.use("seaborn-v0_8")
    plt.rcParams.update(_rc_params())

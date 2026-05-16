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

"""Primitive display methods."""

from __future__ import annotations

from typing import Any

from .cards import (
    detail_card,
    executive_summary_card,
    formula_card,
    section_card,
)
from .comparison import decision_grid
from .primitives import (
    EXECUTIVE_KPI_VALUE_FONT_SIZE,
    danger_box,
    info_box,
    note_block,
    success_box,
    warning_box,
)
from .tables import (
    metric_table,
    sample_table,
)


class _PrimitivesMixin:
    def __call__(self, html: str) -> None:
        """Display any HTML string directly."""
        # noinspection PyPep8Naming
        from IPython.display import HTML as IPyHTML
        from IPython.display import display as ipy_display

        ipy_display(IPyHTML(html))

    @staticmethod
    def markdown(text: str) -> None:
        """Display a rendered markdown string."""
        from IPython.display import Markdown as IPyMarkdown
        from IPython.display import display as ipy_display

        ipy_display(IPyMarkdown(text))

    def info(self, text: str, *, accent: str | None = None) -> None:
        self(info_box(text, accent=accent))

    def warning(self, text: str) -> None:
        self(warning_box(text))

    def success(self, text: str) -> None:
        self(success_box(text))

    def danger(self, text: str) -> None:
        self(danger_box(text))

    def section(
        self,
        title: str,
        body: str = "",
        *,
        accent: str | None = None,
        subtitle: str | None = None,
    ) -> None:
        self(section_card(title, body, accent=accent, subtitle=subtitle))

    def formula(
        self,
        title: str,
        expression: str,
        *,
        result: str | None = None,
        accent: str | None = None,
    ) -> None:
        self(formula_card(title, expression, result=result, accent=accent))

    def note(self, text: str, *, compact: bool = False) -> None:
        self(note_block(text, compact=compact))

    def executive(
        self,
        title: str,
        metrics: list[tuple[str, str, str]],
        *,
        accent: str | None = None,
        footer: str | None = None,
        value_font_size: str = EXECUTIVE_KPI_VALUE_FONT_SIZE,
    ) -> None:
        self(
            executive_summary_card(
                title,
                metrics,
                accent=accent,
                footer=footer,
                value_font_size=value_font_size,
            )
        )

    def detail(
        self, title: str, items: list[str], *, accent: str | None = None
    ) -> None:
        self(detail_card(title, items, accent=accent))

    def metrics(
        self,
        rows: list[tuple[str, str, str | None]],
        *,
        title: str = "Metrics",
        metric_header: str = "Metric",
        value_header: str = "Value",
    ) -> None:
        self(
            metric_table(
                rows,
                title=title,
                metric_header=metric_header,
                value_header=value_header,
            )
        )

    def samples(
        self,
        headers: tuple[str, ...],
        rows: list[tuple[str, ...]],
        *,
        title: str = "Sample Data",
        description: str | None = None,
        footer: str | None = None,
    ) -> None:
        self(
            sample_table(
                headers, rows, title=title, description=description, footer=footer
            )
        )

    def grid(
        self,
        items: list[dict[str, Any]],
        *,
        title: str | None = None,
        footer: str | None = None,
    ) -> None:
        self(decision_grid(items, title=title, footer=footer))

    # ── Side-by-side layout ──────────────────────────────────────────

    def columns(
        self,
        *html_blocks: str,
        gap: str = "16px",
        min_width: str = "250px",
    ) -> None:
        """Display multiple HTML blocks side by side in a flex row.

        Args:
            *html_blocks: Pre-rendered HTML strings, one per column.
            gap: CSS gap between columns (default ``16px``).
            min_width: Minimum column width before wrapping (default ``300px``).
        """
        items = "".join(
            f'<div style="flex:1;min-width:{min_width};">{h}</div>' for h in html_blocks
        )
        self(
            f'<div style="display:flex;flex-wrap:wrap;gap:{gap};align-items:flex-start;">'
            f"{items}</div>"
        )

    # ── HTML-returning variants (use with show.columns) ──────────────

    @staticmethod
    def metrics_html(
        rows: list[tuple[str, str, str | None]],
        *,
        title: str = "Metrics",
        metric_header: str = "Metric",
        value_header: str = "Value",
    ) -> str:
        """Return the metrics table as an HTML string without displaying."""
        return metric_table(
            rows, title=title, metric_header=metric_header, value_header=value_header
        )

    @staticmethod
    def note_html(text: str, *, compact: bool = False) -> str:
        """Return a note block as an HTML string without displaying."""
        return note_block(text, compact=compact)

    @staticmethod
    def info_html(text: str, *, accent: str | None = None) -> str:
        """Return an info box as an HTML string without displaying."""
        return info_box(text, accent=accent)

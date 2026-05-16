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
Glossary helpers for notebook-friendly rendering.

Reads the central ``notebooks/GLOSSARY.ipynb`` notebook and converts glossary
terms into a tabular representation that is easy to read in Jupyter output.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pandas as pd

_DEFAULT_GLOSSARY_PATH = (
    Path(__file__).resolve().parents[3] / "notebooks" / "GLOSSARY.ipynb"
)


def _normalize_text(value: str) -> str:
    """Normalize text for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _extract_term_heading(line: str) -> str | None:
    """Extract a glossary term heading from a markdown line."""
    m = re.match(r"^###\s+(.+?)\s*$", line)
    if m:
        return m.group(1).strip()

    m = re.match(r"^\*\*(.+?)\*\*\s*$", line)
    if not m:
        return None

    candidate = m.group(1).strip()
    # Ignore emphasized labels like "Why \"Portfolio\"?" and table labels.
    if candidate.endswith(":") or len(candidate) > 100:
        return None
    return candidate


def _clean_definition(lines: list[str]) -> str:
    """Condense multi-line markdown text to a single readable sentence block."""
    joined = " ".join(part.strip() for part in lines if part.strip())
    return re.sub(r"\s+", " ", joined).strip()


def _raw_lines_from_path(path: Path) -> list[str]:
    """Extract raw text lines from a glossary path (.ipynb or .md)."""
    if path.suffix == ".ipynb":
        nb = json.loads(path.read_text(encoding="utf-8"))
        md_lines: list[str] = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "markdown":
                md_lines.extend(line.rstrip("\n") for line in cell.get("source", []))
                md_lines.append("")  # blank line between cells
        return md_lines
    return path.read_text(encoding="utf-8").splitlines()


def _flush_term(
    current_term: str | None,
    current_section: str,
    buffer: list[str],
    rows: list[dict[str, str]],
) -> list[str]:
    """Flush current term buffer into rows; returns a new empty buffer."""
    if current_term is not None:
        definition = _clean_definition(buffer)
        if definition:
            rows.append(
                {
                    "Section": current_section,
                    "Term": current_term,
                    "Definition": definition,
                }
            )
    return []


def _should_skip_glossary_line(stripped: str) -> bool:
    return not stripped or stripped == "---" or stripped.startswith("# ")


def _term_matches_tokens(entry: str, tokens: list[str]) -> bool:
    normalized = _normalize_text(entry)
    return any(token in normalized or normalized in token for token in tokens)


def _filter_by_sections(
    df: pd.DataFrame, include_sections: Iterable[str]
) -> pd.DataFrame:
    normalized = {s.strip().lower() for s in include_sections if s.strip()}
    return df[df["Section"].str.lower().isin(normalized)]


def _filter_by_terms(df: pd.DataFrame, include_terms: Iterable[str]) -> pd.DataFrame:
    tokens = [_normalize_text(t) for t in include_terms if t.strip()]
    return df[df["Term"].apply(_term_matches_tokens, args=(tokens,))]


def _parse_glossary_lines(raw_lines: list[str]) -> list[dict[str, str]]:
    """Walk raw text lines and build the list of glossary row dicts."""
    current_section = "General"
    current_term: str | None = None
    buffer: list[str] = []
    rows: list[dict[str, str]] = []
    for raw in raw_lines:
        stripped = raw.rstrip().strip()
        if _should_skip_glossary_line(stripped):
            continue
        if stripped.startswith("## "):
            buffer = _flush_term(current_term, current_section, buffer, rows)
            current_section = stripped[3:].strip()
            current_term = current_section
            continue
        term = _extract_term_heading(stripped)
        if term is not None:
            buffer = _flush_term(current_term, current_section, buffer, rows)
            current_term = term
            continue
        if current_term is None:
            continue
        if stripped.startswith("|"):
            continue
        buffer.append(stripped)
    _flush_term(current_term, current_section, buffer, rows)
    return rows


def load_glossary(
    glossary_path: str | Path | None = None,
    include_terms: Iterable[str] | None = None,
    include_sections: Iterable[str] | None = None,
) -> pd.DataFrame:
    """
    Parse ``GLOSSARY.md`` into a DataFrame.

    Args:
        glossary_path: Optional path override for glossary source.
        include_terms: Optional iterable of term fragments to filter for.
        include_sections: Optional iterable of section names to filter for.

    Returns:
        DataFrame with columns: ``Section``, ``Term``, ``Definition``.
    """
    path = Path(glossary_path) if glossary_path is not None else _DEFAULT_GLOSSARY_PATH
    if not path.exists():
        raise FileNotFoundError(f"Glossary file not found: {path}")

    raw_lines = _raw_lines_from_path(path)
    rows = _parse_glossary_lines(raw_lines)

    df = pd.DataFrame(rows, columns=["Section", "Term", "Definition"])
    if df.empty:
        return df

    if include_sections:
        df = _filter_by_sections(df, include_sections)

    if include_terms:
        df = _filter_by_terms(df, include_terms)

    return df.reset_index(drop=True)


def display_glossary(
    include_terms: Iterable[str] | None = None,
    include_sections: Iterable[str] | None = None,
    glossary_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Render glossary entries in notebook-friendly tabular format.

    Args:
        include_terms: Optional term filter.
        include_sections: Optional section filter.
        glossary_path: Optional path override.

    Returns:
        The rendered glossary DataFrame.
    """
    df = load_glossary(
        glossary_path=glossary_path,
        include_terms=include_terms,
        include_sections=include_sections,
    )

    if df.empty:
        print("No glossary entries matched the provided filters.")
        return df

    try:
        from IPython.display import display
    except ImportError:
        display = None  # type: ignore[assignment]

    if display is not None:
        # noinspection PyCallingNonCallableInspection
        display(df)
    else:
        print(df.to_string(index=False))

    return df


def glossary_widget(
    include_sections: Iterable[str] | None = None,
    glossary_path: str | Path | None = None,
    title: str = "📖 Glossary — Key Terms",
) -> object:
    """
    Return a collapsible ipywidgets Accordion with glossary terms.

    Groups terms by section. Each accordion panel renders one section as a
    styled HTML table with Term and Definition columns.

    Falls back to ``display_glossary()`` when ipywidgets is not installed.

    Args:
        include_sections: Optional section filter (e.g. ["Financial Risk", "Delivery"]).
        glossary_path:    Optional path override for the glossary source.
        title:            Label shown above the accordion.

    Returns:
        An ipywidgets VBox (or None if running outside a notebook).

    Example::

        from fhs.notebook.glossary import glossary_widget
        glossary_widget()          # all sections
        glossary_widget(include_sections=["Financial Risk"])
    """

    def section_html(sec_df: pd.DataFrame) -> str:
        display_df = sec_df.loc[:, ["Term", "Definition"]].fillna("").astype(str)
        row_fragments = []
        for term, definition in display_df.itertuples(index=False, name=None):
            term_text = cast(str, term)
            definition_text = cast(str, definition)
            row_fragments.append(
                f"<tr>"
                f"<td style='padding:6px 12px;font-weight:600;vertical-align:top;"
                f"white-space:nowrap;color:#1565c0'>{term_text}</td>"
                f"<td style='padding:6px 12px;vertical-align:top'>{definition_text}</td>"
                f"</tr>"
            )
        rows = "".join(row_fragments)
        return (
            "<table style='border-collapse:collapse;width:100%;font-size:13px'>"
            f"<thead><tr>"
            f"<th style='padding:6px 12px;text-align:left;background:#e3f2fd;"
            f"color:#0d47a1;width:200px'>Term</th>"
            f"<th style='padding:6px 12px;text-align:left;background:#e3f2fd;"
            f"color:#0d47a1'>Definition</th>"
            f"</tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    df = load_glossary(
        glossary_path=glossary_path,
        include_sections=include_sections,
    )

    if df.empty:
        print("No glossary entries matched the provided filters.")
        return None

    try:
        import ipywidgets as widgets
        from IPython.display import HTML, display
    except ImportError:
        display_glossary(include_sections=include_sections, glossary_path=glossary_path)
        return None

    sections = df["Section"].unique().tolist()
    panels = []
    for section in sections:
        section_df = df[df["Section"] == section]
        html_out = widgets.Output()
        with html_out:
            display(HTML(section_html(section_df)))
        panels.append(html_out)

    accordion = widgets.Accordion(children=panels)
    for i, section in enumerate(sections):
        count = len(df[df["Section"] == section])
        accordion.set_title(i, f"{section}  ({count} terms)")
    accordion.selected_index = None  # collapsed by default

    header = widgets.HTML(
        f"<h4 style='margin:8px 0 4px 0;color:#0d47a1'>{title}</h4>"
        f"<p style='margin:0 0 8px 0;font-size:12px;color:#555'>"
        f"Click a section to expand. Covers {len(df)} terms across {len(sections)} sections.</p>"
    )

    vbox = widgets.VBox(
        [header, accordion],
        layout=widgets.Layout(
            border="1px solid #bbdefb", padding="8px", margin="8px 0"
        ),
    )
    display(vbox)
    return vbox


__all__ = ["display_glossary", "glossary_widget", "load_glossary"]

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
Notebook facade — simplified entry point for notebooks (presentation layer).

This module provides the main `load_scenario()` function that notebooks use.
It hides complexity and provides a clean, Apple/Google-style UX.
"""

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from fhs.application.dtos import ScenarioContext
from fhs.application.scenario_service import ScenarioService
from fhs.core.model.events import EventBus, EventLogger
from fhs.notebook.glossary import display_glossary, glossary_widget, load_glossary

# Register global event logger for audit trail
_DEFAULT_CONFIG_DIR = (
    Path(__file__).parent.parent.parent.parent / "notebooks" / "config"
)
_LOG_DIR = _DEFAULT_CONFIG_DIR.parent / "logs"
EventBus.register(EventLogger(log_file=_LOG_DIR / "scenario_changes.log"))

# Try to import notebook display tools (optional dependency)
try:
    import ipywidgets as widgets
    from IPython.display import display

    _HAS_WIDGETS = True
except ImportError:
    widgets = None  # type: ignore[assignment]
    display = None  # type: ignore[assignment]
    _HAS_WIDGETS = False

try:
    from fhs.presentation.notebook import COLORS, show
    from fhs.presentation.notebook.widgets.cards import executive_summary_card

    _HAS_NOTEBOOK_STYLE = True
except ImportError:
    COLORS = None  # type: ignore[assignment]
    show = None  # type: ignore[assignment]
    executive_summary_card = None  # type: ignore[assignment]
    _HAS_NOTEBOOK_STYLE = False


def markdown(text: str) -> None:
    """Render a markdown string in the notebook."""
    if _HAS_NOTEBOOK_STYLE:
        show.markdown(text)
    else:
        try:
            from IPython.display import Markdown, display

            display(Markdown(text))
        except ImportError:
            print(text)


@dataclass(frozen=True)
class NotebookSetupContext:
    """Optional setup result carrying central scenario artifacts for notebooks.

    Provides shortcuts so notebooks need only::

        from fhs.notebook import notebook_setup
        setup = notebook_setup("blockchain")

    and can then access ``setup.show``, ``setup.colors``, ``setup.features``, etc.
    without additional imports.
    """

    # noinspection PyTypeHintsInspection
    scenario: ScenarioContext | None = None

    # ── Presentation shortcuts ───────────────────────────────────────────────

    @property
    def show(self):
        """FHS display facade (show.info, show.warning, show.executive, …)."""
        if _HAS_NOTEBOOK_STYLE:
            from fhs.presentation.notebook import show as _show

            return _show
        return None

    # noinspection PyPep8Naming
    @property
    def colors(self):
        """FHS colour palette (COLORS.primary, COLORS.danger, …)."""
        if _HAS_NOTEBOOK_STYLE:
            from fhs.presentation.notebook import COLORS as _colors

            return _colors
        return None

    @property
    def fig(self):
        """FHS default figure dimensions (FIG.width, FIG.height)."""
        if _HAS_NOTEBOOK_STYLE:
            from fhs.presentation.notebook import FIG

            return FIG
        return None

    def __getattr__(self, name: str) -> Any:
        if name == "COLORS":
            return self.colors
        if name == "FIG":
            return self.fig
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")

    # ── Scenario shortcuts ───────────────────────────────────────────────────

    @property
    def features(self):
        """Feature list from loaded scenario, or empty list."""
        if self.scenario is None:
            return []
        return self.scenario.features

    @property
    def features_by_key(self):
        """Feature dict {key: Feature} from loaded scenario, or empty dict."""
        if self.scenario is None:
            return {}
        return self.scenario.features_by_key

    @property
    def risk_model(self):
        """Shortcut to the configured risk model when a scenario is loaded."""
        if self.scenario is None:
            return None
        return self.scenario.risk_model

    @property
    def delivery_config(self):
        """Shortcut to the delivery risk configuration when a scenario is loaded."""
        if self.scenario is None:
            return None
        return self.scenario.delivery_config


def notebook_setup(
    scenario_id: str | None = None,
    editable: bool = False,
    show_status: bool = True,
    path: str | Path | None = None,
) -> NotebookSetupContext:
    """
    One-line setup for notebooks.

    Configures:
    - Matplotlib inline mode
    - Warning filters (FutureWarning, DeprecationWarning)
    - FHS presentation style
    - Python path for local imports

    If ``scenario_id`` is provided, this helper also loads the scenario and returns
    a context object with shortcuts to ``risk_model`` and ``delivery_config``.

    Example:
        >>> from fhs.notebook import notebook_setup
        >>> notebook_setup()

        >>> setup = notebook_setup("blockchain")
        >>> loaded = setup.scenario
        >>> risk_model = setup.risk_model
        >>> delivery_config = setup.delivery_config
    """
    # Enable matplotlib inline
    try:
        get_ipython_fn = getattr(
            importlib.import_module("IPython"), "get_ipython", None
        )
        ipython = get_ipython_fn() if callable(get_ipython_fn) else None
        run_magic = (
            getattr(ipython, "run_line_magic", None) if ipython is not None else None
        )
        if callable(run_magic):
            run_magic("matplotlib", "inline")
    except ImportError:
        pass

    # Filter warnings
    import warnings

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Apply FHS notebook style if available
    if _HAS_NOTEBOOK_STYLE:
        from fhs.presentation.notebook import setup_style

        setup_style()

    # No sys.path manipulation needed - package is properly installed
    if scenario_id is None:
        return NotebookSetupContext()

    scenario = load_scenario(
        scenario_id,
        editable=editable,
        show_status=show_status,
        path=path,
    )
    return NotebookSetupContext(scenario=scenario)


# Singleton service (initialized once per session)
_SERVICE = None


def _get_service() -> ScenarioService:
    """Get or create singleton scenario service."""
    global _SERVICE

    if _SERVICE is None:
        # Use ScenarioService with default repository (no direct infra import)
        _SERVICE = ScenarioService.create_default(config_dir=_DEFAULT_CONFIG_DIR)

    return _SERVICE


def load_scenario(
    scenario_id: str,
    editable: bool = False,
    show_status: bool = True,
    path: str | Path | None = None,
) -> ScenarioContext:
    """
    Load a scenario for notebook use.

    This is the main entry point for notebooks.

    Args:
        scenario_id: Scenario identifier (e.g., "blockchain")
        editable: Show configuration form (default: False)
        show_status: Display status cards (default: True)
        path: Optional path override for config files (mostly for testing)

    Returns:
        ScenarioContext with features, budget, strategy, etc.

    Example:
        >>> # In notebook 02 (editable):
        >>> scenario = load_scenario("blockchain", editable=True)

        >>> # In notebooks A01-A03 (read-only):
        >>> scenario = load_scenario("blockchain")

        >>> # Access features
        >>> len(scenario.features)
        3
        >>> scenario.features_by_key["H1"].name
        'H1: Simplified UI'
    """
    service = _get_service()
    context = service.load_scenario(scenario_id, path=path)

    if show_status:
        _show_status_card(context)

    if editable:
        _show_config_form(context)

    return context


# noinspection PyCallingNonCallableInspection
def _show_status_card(context: ScenarioContext) -> None:
    """Display Material Design status card."""
    if not _HAS_NOTEBOOK_STYLE:
        # Fallback to plain print
        print(f"Scenario loaded: {context.scenario_id}")
        print(f"Features: {len(context.features)}")
        print(f"Budget: EUR {context.budget:,.0f}")
        return

    feature_count = len(context.features)
    budget_k = context.budget / 1000

    # Create an executive summary card for a more professional look
    metrics = [
        (f"{feature_count}", "Features", COLORS.primary),
        (f"€{budget_k:,.0f}k", "Budget", COLORS.secondary),
    ]

    # Add a sparkline-like indicator for config source
    source_label = "Local YAML"
    if context.config_source == "saved":
        source_label = "User Config (JSON)"

    footer = (
        f"<b>Source:</b> <code>{context.config_path}</code><br>"
        f"<b>Type:</b> {source_label}"
    )

    if not callable(executive_summary_card):
        print(f"Scenario loaded: {context.scenario_id}")
        print(f"Features: {feature_count}")
        print(f"Budget: EUR {context.budget:,.0f}")
        return

    card_html = executive_summary_card(
        title=f"Scenario: {context.scenario_id.capitalize()}",
        metrics=metrics,
        accent=COLORS.primary,
        footer=footer,
    )

    if show is not None:
        show_fn = cast(Any, show)
        show_fn(card_html)
    else:
        print(f"Scenario loaded: {context.scenario_id}")
        print(f"Features: {feature_count}")
        print(f"Budget: EUR {context.budget:,.0f}")


def _show_config_form(context: ScenarioContext) -> None:
    """
    Display editable configuration form using ipywidgets.
    """
    if not _HAS_WIDGETS:
        if not _HAS_NOTEBOOK_STYLE:
            print("\n🔧 Configuration Form (ipywidgets not installed)")
            print(f"Edit: {context.config_path}")
            return

        show.info(
            "🔧 <b>Configuration Form</b><br>"
            f"<i>ipywidgets not installed. Edit values in: <code>{context.config_path}</code></i>",
            accent=COLORS.warning,
        )
        return

    # Create widgets for budget
    budget_slider = widgets.FloatSlider(
        value=context.budget,
        min=10000,
        max=500000,
        step=5000,
        description="Budget (EUR):",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="50%"),
        tooltip=(
            "Total development budget for all features in this scenario. "
            "Range: €10,000–€500,000. Used by the portfolio optimizer."
        ),
    )

    discount_rate_slider = widgets.FloatSlider(
        value=context.discount_rate,
        min=0.0,
        max=0.30,
        step=0.01,
        description="Discount Rate:",
        readout_format=".0%",
        style={"description_width": "initial"},
        layout=widgets.Layout(width="50%"),
        tooltip=(
            "Annual discount rate for NPV / multi-year calculations. "
            "Range: 0–30%. Typical: 8–12% (corporate hurdle rate). "
            "Higher = future cash flows worth less today."
        ),
    )

    feature_widgets = []
    for feature in context.features:
        name_label = widgets.HTML(f"<b>{feature.name}</b>")
        users_slider = widgets.IntSlider(
            value=feature.expected_users,
            min=100,
            max=100000,
            step=100,
            description="Users:",
            tooltip=(
                "Expected number of users who will encounter this feature. "
                "Range: 100–100,000. "
                "Source: traffic analytics, segment analysis, or product roadmap."
            ),
        )
        conv_slider = widgets.FloatSlider(
            value=feature.conversion_rate,
            min=0.01,
            max=1.0,
            step=0.01,
            description="Conv. Rate:",
            tooltip=(
                "Fraction of users completing the desired action (0.01–1.0). "
                "Benchmarks: e-commerce checkout 2–5% (0.02–0.05), "
                "SaaS trial→paid 10–25% (0.10–0.25), upsell 20–40% (0.20–0.40). "
                "Use past A/B test data when available."
            ),
        )
        uncert_slider = widgets.FloatSlider(
            value=feature.uncertainty,
            min=0.0,
            max=1.0,
            step=0.05,
            description="Uncertainty:",
            tooltip=(
                "Confidence in your assumptions (0.0–1.0 = ±3σ range). "
                "Low 0.10–0.15: strong historical data, mature market. "
                "Medium 0.25–0.35: some unknowns, new user segment. "
                "High 0.40–0.50: brand new feature, unstable market. "
                "⚠ Represents ±3σ span, not ±1σ."
            ),
        )
        value_input = widgets.FloatText(
            value=feature.business_value_per_conversion,
            description="Value / Conv. (EUR):",
            style={"description_width": "initial"},
            tooltip=(
                "Business value generated per converted user, in EUR. "
                "Example: average order value, subscription price, or LTV contribution. "
                "Multiply by conversion_rate × expected_users to get expected total value."
            ),
        )
        installment_years_input = widgets.BoundedIntText(
            value=feature.installment_years,
            min=1,
            max=30,
            step=1,
            description="Installment (Years):",
            style={"description_width": "initial"},
            tooltip=(
                "Number of years over which development cost is spread (1–30). "
                "1 = full cost in Year 1. "
                "Used for capital budgeting and NPV calculations."
            ),
        )
        growth_slider = widgets.FloatSlider(
            value=feature.annual_growth_rate,
            min=-0.5,
            max=1.0,
            step=0.05,
            description="Annual Growth:",
            tooltip=(
                "Year-over-year growth rate for multi-year simulations (-0.5 to 1.0). "
                "0.0 = flat. 0.10 = 10% annual growth. -0.20 = 20% annual decline. "
                "Typical SaaS growth: 0.15–0.30."
            ),
        )

        box = widgets.VBox(
            [
                name_label,
                users_slider,
                conv_slider,
                uncert_slider,
                value_input,
                installment_years_input,
                growth_slider,
            ]
        )
        feature_widgets.append(
            {
                "box": box,
                "users": users_slider,
                "conversion": conv_slider,
                "uncertainty": uncert_slider,
                "business_value": value_input,
                "installment_years": installment_years_input,
                "growth": growth_slider,
            }
        )

    save_button = widgets.Button(
        description="Save For All Notebooks",
        button_style="success",
        icon="save",
        layout=widgets.Layout(margin="10px 0 0 0"),
    )

    status_output = widgets.Output()

    def on_save_clicked(_b):
        with status_output:
            status_output.clear_output()
            try:
                # Update features from widget values
                updated_features = []
                for idx, feat in enumerate(context.features):
                    widget_refs = feature_widgets[idx]
                    f_dict = feat.model_dump()
                    f_dict["expected_users"] = widget_refs["users"].value
                    f_dict["conversion_rate"] = widget_refs["conversion"].value
                    f_dict["uncertainty"] = widget_refs["uncertainty"].value
                    f_dict["business_value_per_conversion"] = widget_refs[
                        "business_value"
                    ].value
                    f_dict["installment_years"] = widget_refs["installment_years"].value
                    f_dict["annual_growth_rate"] = widget_refs["growth"].value
                    from fhs.core.model import Feature

                    updated_features.append(Feature(**f_dict))

                # Save via service
                service = _get_service()
                service.save_scenario(
                    scenario_id=context.scenario_id,
                    features=updated_features,
                    budget=budget_slider.value,
                    strategy=context.strategy,
                    metadata={"config_source": context.config_source},
                    discount_rate=discount_rate_slider.value,
                )

                version_count = len(service.list_versions(context.scenario_id))
                print(f"Saved '{context.scenario_id}' for all notebooks.")
                print(f"Config: {context.config_path}")
                print(f"🕘 Versions available: {version_count}")
                print("↻ Re-run dependent notebook cells to load updated values.")
            except Exception as e:  # noqa: BLE001
                print(f"❌ Error saving scenario: {e}")

    save_button.on_click(on_save_clicked)

    # Accordion for features to save space (Progressive Disclosure)
    accordion = widgets.Accordion(
        children=[widgets.VBox([item["box"] for item in feature_widgets])]
    )
    accordion.set_title(0, "Feature Details")

    form = widgets.VBox(
        [
            widgets.HTML("<h3>🔧 Configuration Form</h3>"),
            budget_slider,
            discount_rate_slider,
            accordion,
            save_button,
            status_output,
        ],
        layout=widgets.Layout(
            border="1px solid #ccc", padding="10px", margin="10px 0 20px 0"
        ),
    )

    if callable(display):
        display(form)


__all__ = [
    "NotebookSetupContext",
    "display_glossary",
    "glossary_widget",
    "load_glossary",
    "load_scenario",
    "markdown",
    "notebook_setup",
]

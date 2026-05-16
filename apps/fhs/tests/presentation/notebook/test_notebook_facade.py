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

"""Tests for the notebook facade helpers in fhs.notebook."""

import importlib
from types import SimpleNamespace

import numpy as np

import fhs.notebook as notebook
from fhs.application.dtos import ScenarioContext
from fhs.core.model import DeliveryRiskConfig, Feature, ScenarioRiskModel
from fhs.core.model.events import EventBus


class _DummyService:
    def __init__(self, context: ScenarioContext):
        self.context = context
        self.calls = []

    def load_scenario(self, scenario_id, path=None):
        self.calls.append((scenario_id, path))
        return self.context


class _ShowRecorder:
    def __init__(self):
        self.calls = []

    def __call__(self, html):
        self.calls.append(html)

    def info(self, message, accent=None):
        self.calls.append((message, accent))


def _context() -> ScenarioContext:
    return ScenarioContext(
        scenario_id="blockchain",
        features=[
            Feature(
                name="H1: Simplified UI",
                expected_users=1000,
                conversion_rate=0.15,
                uncertainty=0.2,
                business_value_per_conversion=41.6,
            )
        ],
        budget=100000,
        discount_rate=0.10,
        strategy={"opt": {"kind": "exact"}},
        weights={"value": 1.0},
        dependency_matrix=np.eye(1),
        config_path="cfg.yml",
        config_source="saved",
        exam_report={"passed": True, "checks": [{"passed": True}]},
        risk_model=ScenarioRiskModel(),
        delivery_config=DeliveryRiskConfig(),
    )


def test_load_scenario_triggers_status_and_form(monkeypatch):
    ctx = _context()
    svc = _DummyService(ctx)
    marks = {"status": 0, "form": 0}

    monkeypatch.setattr(notebook, "_get_service", lambda: svc)
    monkeypatch.setattr(
        notebook,
        "_show_status_card",
        lambda context: marks.__setitem__("status", marks["status"] + 1),
    )
    monkeypatch.setattr(
        notebook,
        "_show_config_form",
        lambda context: marks.__setitem__("form", marks["form"] + 1),
    )

    result = notebook.load_scenario("blockchain", editable=True, show_status=True)

    assert result is ctx
    assert svc.calls == [("blockchain", None)]
    assert marks == {"status": 1, "form": 1}


def test_load_scenario_skips_ui_when_disabled(monkeypatch):
    ctx = _context()
    svc = _DummyService(ctx)

    monkeypatch.setattr(notebook, "_get_service", lambda: svc)
    monkeypatch.setattr(
        notebook,
        "_show_status_card",
        lambda context: (_ for _ in ()).throw(AssertionError("must not be called")),
    )
    monkeypatch.setattr(
        notebook,
        "_show_config_form",
        lambda context: (_ for _ in ()).throw(AssertionError("must not be called")),
    )

    result = notebook.load_scenario("blockchain", editable=False, show_status=False)

    assert result is ctx


def test_notebook_setup_returns_empty_context_without_scenario_id(monkeypatch):
    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", False)

    setup = notebook.notebook_setup()

    assert setup.scenario is None
    assert setup.risk_model is None
    assert setup.delivery_config is None


def test_notebook_setup_loads_scenario_and_exposes_central_artifacts(monkeypatch):
    ctx = _context()
    calls = []

    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", False)

    def _fake_load_scenario(*args, **kwargs):
        calls.append((args, kwargs))
        return ctx

    monkeypatch.setattr(notebook, "load_scenario", _fake_load_scenario)

    setup = notebook.notebook_setup(
        "blockchain",
        editable=True,
        show_status=False,
        path="cfg.yml",
    )

    assert setup.scenario is ctx
    assert setup.risk_model is ctx.risk_model
    assert setup.delivery_config is ctx.delivery_config
    assert calls == [
        (
            ("blockchain",),
            {
                "editable": True,
                "show_status": False,
                "path": "cfg.yml",
            },
        )
    ]


def test_show_status_card_fallback_prints(capsys, monkeypatch):
    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", False)

    notebook._show_status_card(_context())

    out = capsys.readouterr().out
    assert "Scenario loaded" in out
    assert "Features" in out
    assert "Budget" in out


def test_show_status_card_uses_show_without_widgets(monkeypatch):
    show_recorder = _ShowRecorder()

    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", True)
    monkeypatch.setattr(notebook, "_HAS_WIDGETS", False)
    monkeypatch.setattr(notebook, "show", show_recorder, raising=False)
    monkeypatch.setattr(
        notebook,
        "COLORS",
        SimpleNamespace(primary="#111", secondary="#222", warning="#f90"),
        raising=False,
    )
    monkeypatch.setattr(
        notebook,
        "executive_summary_card",
        lambda **kwargs: "<card>",
        raising=False,
    )

    notebook._show_status_card(_context())

    assert show_recorder.calls == ["<card>"]


def test_show_config_form_fallback_without_widgets_and_style(capsys, monkeypatch):
    monkeypatch.setattr(notebook, "_HAS_WIDGETS", False)
    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", False)

    notebook._show_config_form(_context())

    out = capsys.readouterr().out
    assert "Configuration Form" in out
    assert "cfg.yml" in out


def test_show_config_form_fallback_without_widgets_with_style(monkeypatch):
    show_recorder = _ShowRecorder()

    monkeypatch.setattr(notebook, "_HAS_WIDGETS", False)
    monkeypatch.setattr(notebook, "_HAS_NOTEBOOK_STYLE", True)
    monkeypatch.setattr(notebook, "show", show_recorder, raising=False)
    monkeypatch.setattr(
        notebook,
        "COLORS",
        SimpleNamespace(primary="#111", secondary="#222", warning="#f90"),
        raising=False,
    )

    notebook._show_config_form(_context())

    assert len(show_recorder.calls) == 1
    message, accent = show_recorder.calls[0]
    assert "ipywidgets not installed" in message
    assert accent == "#f90"


def test_show_config_form_widget_branch_and_save(monkeypatch, capsys):
    class _Layout:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class _BaseWidget:
        def __init__(self, value=None, children=None, **kwargs):
            self.value = value
            self.children = children or []
            self.kwargs = kwargs

    class _HTML(_BaseWidget):
        pass

    class _Slider(_BaseWidget):
        pass

    class _VBox(_BaseWidget):
        def __init__(self, children=None, **kwargs):
            super().__init__(children=children or [], **kwargs)

    class _Button(_BaseWidget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._handler = None

        def on_click(self, handler):
            self._handler = handler

    class _Output(_BaseWidget):
        @staticmethod
        def clear_output():
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Accordion(_BaseWidget):
        def __init__(self, children=None, **kwargs):
            super().__init__(children=children or [], **kwargs)
            self.titles = {}

        def set_title(self, index, title):
            self.titles[index] = title

    class _Widgets:
        Layout = _Layout
        HTML = _HTML
        FloatSlider = _Slider
        FloatText = _Slider
        IntSlider = _Slider
        BoundedIntText = _Slider
        VBox = _VBox
        Button = _Button
        Output = _Output
        Accordion = _Accordion

    class _SaveService:
        def __init__(self):
            self.saved = []

        def save_scenario(self, **kwargs):
            self.saved.append(kwargs)

        @staticmethod
        def list_versions(_scenario_id):
            return ["v1", "v2"]

    saved_service = _SaveService()
    displayed = []

    monkeypatch.setattr(notebook, "_HAS_WIDGETS", True)
    monkeypatch.setattr(notebook, "widgets", _Widgets())
    monkeypatch.setattr(notebook, "display", lambda obj: displayed.append(obj))
    monkeypatch.setattr(notebook, "_get_service", lambda: saved_service)

    notebook._show_config_form(_context())

    # Form is displayed once and includes save button + output widget.
    assert len(displayed) == 1
    form = displayed[0]
    discount_rate_slider = form.children[2]
    accordion = form.children[3]
    feature_box = accordion.children[0].children[0]
    value_input = feature_box.children[4]
    value_input.value = 99.9
    discount_rate_slider.value = 0.12
    save_button = form.children[4]
    assert hasattr(save_button, "_handler")

    # Trigger save callback and verify persistence call.
    save_button._handler(None)
    out = capsys.readouterr().out
    assert "Saved 'blockchain'" in out
    assert len(saved_service.saved) == 1
    assert saved_service.saved[0]["discount_rate"] == 0.12
    saved_feature = saved_service.saved[0]["features"][0]
    assert saved_feature.business_value_per_conversion == 99.9


def test_notebook_reload_does_not_duplicate_event_logger():
    EventBus._handlers.clear()

    reloaded = importlib.reload(notebook)
    assert len(EventBus._handlers) == 1

    importlib.reload(reloaded)
    assert len(EventBus._handlers) == 1

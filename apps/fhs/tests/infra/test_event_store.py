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

"""Tests for SqliteEventStore — persistent domain event storage."""

from __future__ import annotations

import pytest

from fhs.core.model.events import EventBus, ScenarioConfigurationChanged
from fhs.infra.event_store import SqliteEventStore

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path):
    """Fresh SqliteEventStore backed by a temp file."""
    return SqliteEventStore(tmp_path / "events.db")


@pytest.fixture
def event():
    """A minimal ScenarioConfigurationChanged event."""
    return ScenarioConfigurationChanged(
        scenario_id="blockchain",
        changed_by="test_user",
        changes={"budget": 50_000},
    )


# ── Construction ──────────────────────────────────────────────────────────────


def test_db_file_created(tmp_path):
    db = tmp_path / "sub" / "events.db"
    SqliteEventStore(db)
    assert db.exists()


def test_initial_event_count_zero(store):
    assert store.event_count() == 0


# ── Handle / persist ─────────────────────────────────────────────────────────


def test_handle_persists_event(store, event):
    store.handle(event)
    assert store.event_count() == 1


def test_handle_stores_correct_fields(store, event):
    store.handle(event)
    rows = store.all_events()
    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "scenario.configuration.changed"
    assert row["scenario_id"] == "blockchain"
    assert row["changed_by"] == "test_user"
    assert isinstance(row["payload"], dict)


def test_multiple_events_stored_in_order(store):
    for i in range(3):
        store.handle(
            ScenarioConfigurationChanged(
                scenario_id="blockchain",
                changed_by="user",
                changes={"step": i},
            )
        )
    rows = store.all_events()
    assert len(rows) == 3
    assert [r["id"] for r in rows] == [1, 2, 3]


# ── Filter by scenario ────────────────────────────────────────────────────────


def test_events_for_scenario_filters_correctly(store):
    store.handle(ScenarioConfigurationChanged("blockchain", "u", {"x": 1}))
    store.handle(ScenarioConfigurationChanged("other", "u", {"x": 2}))
    bc_events = store.events_for_scenario("blockchain")
    assert len(bc_events) == 1
    assert bc_events[0]["scenario_id"] == "blockchain"


def test_events_for_scenario_empty_when_no_match(store, event):
    store.handle(event)
    assert store.events_for_scenario("nonexistent") == []


# ── Replay ────────────────────────────────────────────────────────────────────


def test_replay_calls_handler_for_each_event(store):
    for _ in range(3):
        store.handle(ScenarioConfigurationChanged("bc", "u", {}))

    received: list[dict] = []

    class Collector:
        @staticmethod
        def handle(d):
            received.append(d)

    n = store.replay(Collector())
    assert n == 3
    assert len(received) == 3


def test_replay_with_scenario_filter(store):
    store.handle(ScenarioConfigurationChanged("bc", "u", {}))
    store.handle(ScenarioConfigurationChanged("other", "u", {}))
    store.handle(ScenarioConfigurationChanged("bc", "u", {}))

    received: list[dict] = []

    class Collector:
        @staticmethod
        def handle(d):
            received.append(d)

    n = store.replay(Collector(), scenario_id="bc")
    assert n == 2
    assert all(r["scenario_id"] == "bc" for r in received)


# ── EventBus integration ──────────────────────────────────────────────────────


def test_eventbus_registration_and_publish(tmp_path):
    store = SqliteEventStore(tmp_path / "bus_events.db")
    EventBus.register(store)

    event = ScenarioConfigurationChanged("blockchain", "bus_user", {"budget": 1000})
    EventBus.publish(event)

    rows = store.all_events()
    assert any(r["scenario_id"] == "blockchain" for r in rows)

    # Cleanup — remove handler to avoid polluting other tests
    EventBus._handlers = [h for h in EventBus._handlers if h != store]


# ── Clear ─────────────────────────────────────────────────────────────────────


def test_clear_removes_all_events(store, event):
    store.handle(event)
    assert store.event_count() == 1
    store.clear()
    assert store.event_count() == 0


# ── Equality / hash (for EventBus dedup) ─────────────────────────────────────


def test_equality_same_path(tmp_path):
    a = SqliteEventStore(tmp_path / "e.db")
    b = SqliteEventStore(tmp_path / "e.db")
    assert a == b


def test_equality_different_path(tmp_path):
    a = SqliteEventStore(tmp_path / "a.db")
    b = SqliteEventStore(tmp_path / "b.db")
    assert a != b


def test_hashable(tmp_path):
    store = SqliteEventStore(tmp_path / "e.db")
    s = {store}
    assert store in s

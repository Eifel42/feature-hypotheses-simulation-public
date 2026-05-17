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

"""Persistent SQLite-backed event store for FHS domain events.

Registers as an ``EventBus`` handler and persists every domain event to a
local SQLite database, enabling:

- Audit trail that survives session restarts
- Event replay for debugging and compliance
- Cross-session scenario change history

Usage::

    from fhs.infra.event_store import SqliteEventStore
    from fhs.core.model.events import EventBus

    store = SqliteEventStore("path/to/events.db")
    EventBus.register(store)

    # Later — retrieve all events:
    for row in store.all_events():
        print(row)

    # Replay events to a handler:
    store.replay(handler=my_handler)

    # Filter by scenario:
    store.replay(scenario_id="blockchain", handler=my_handler)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fhs.core.model.events import DomainEvent

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS domain_events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type    TEXT    NOT NULL,
    timestamp     TEXT    NOT NULL,
    scenario_id   TEXT,
    changed_by    TEXT,
    payload       TEXT    NOT NULL
)
"""

_INSERT_SQL = """
INSERT INTO domain_events (event_type, timestamp, scenario_id, changed_by, payload)
VALUES (?, ?, ?, ?, ?)
"""

_SELECT_ALL_SQL = """
SELECT id, event_type, timestamp, scenario_id, changed_by, payload
FROM domain_events
ORDER BY id ASC
"""

_SELECT_SCENARIO_SQL = """
SELECT id, event_type, timestamp, scenario_id, changed_by, payload
FROM domain_events
WHERE scenario_id = ?
ORDER BY id ASC
"""


class SqliteEventStore:
    """Persistent event handler that writes domain events to a SQLite database.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Created automatically if it does
        not exist (including parent directories).
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── EventBus interface ────────────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SqliteEventStore):
            return NotImplemented
        return self.db_path == other.db_path

    def __hash__(self) -> int:
        return hash(self.db_path)

    def handle(self, event: DomainEvent) -> None:
        """Persist a domain event to the SQLite store."""
        scenario_id = getattr(event, "scenario_id", None)
        changed_by = getattr(event, "changed_by", None)

        # Collect all dataclass fields into a JSON payload
        payload: dict[str, Any] = {}
        for field in event.__dataclass_fields__:  # type: ignore[attr-defined]
            val = getattr(event, field)
            # Ensure serializability
            if isinstance(val, datetime):
                val = val.isoformat()
            payload[field] = val

        with self._connect() as conn:
            conn.execute(
                _INSERT_SQL,
                (
                    event.event_type,
                    event.timestamp.isoformat(),
                    scenario_id,
                    changed_by,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    # ── Query interface ───────────────────────────────────────────────────────

    def all_events(self) -> list[dict[str, Any]]:
        """Return all stored events as a list of dicts (oldest first).

        Returns
        -------
        list[dict]
            Each dict has keys: ``id``, ``event_type``, ``timestamp``,
            ``scenario_id``, ``changed_by``, ``payload`` (dict).
        """
        with self._connect() as conn:
            rows = conn.execute(_SELECT_ALL_SQL).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def events_for_scenario(self, scenario_id: str) -> list[dict[str, Any]]:
        """Return all events for a specific scenario (oldest first).

        Parameters
        ----------
        scenario_id:
            Scenario identifier to filter by (e.g. ``"blockchain"``).
        """
        with self._connect() as conn:
            rows = conn.execute(_SELECT_SCENARIO_SQL, (scenario_id,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def replay(
        self,
        handler: Any,
        *,
        scenario_id: str | None = None,
    ) -> int:
        """Replay stored events to a handler.

        Parameters
        ----------
        handler:
            Any object with a ``handle(event_dict)`` method.  The dict
            passed to ``handle`` has the same keys as :meth:`all_events`.
        scenario_id:
            When given, only events for that scenario are replayed.

        Returns
        -------
        int
            Number of events replayed.
        """
        events = (
            self.events_for_scenario(scenario_id)
            if scenario_id is not None
            else self.all_events()
        )
        for event_dict in events:
            handler.handle(event_dict)
        return len(events)

    def clear(self) -> None:
        """Delete all stored events.  Useful for tests or fresh starts."""
        with self._connect() as conn:
            conn.execute("DELETE FROM domain_events")

    def event_count(self) -> int:
        """Return the total number of stored events."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM domain_events").fetchone()
        return int(row[0]) if row else 0

    # ── Internals ─────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE_SQL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    @staticmethod
    def _row_to_dict(row: tuple) -> dict[str, Any]:
        id_, event_type, timestamp, scenario_id, changed_by, payload_json = row
        return {
            "id": id_,
            "event_type": event_type,
            "timestamp": timestamp,
            "scenario_id": scenario_id,
            "changed_by": changed_by,
            "payload": json.loads(payload_json),
        }

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

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar


@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""

    timestamp: datetime
    event_type: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ScenarioConfigurationChanged(DomainEvent):
    """Fired when scenario configuration is modified."""

    scenario_id: str
    changed_by: str
    changes: dict[str, Any]

    def __init__(
        self,
        scenario_id: str,
        changed_by: str,
        changes: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ):
        object.__setattr__(self, "scenario_id", scenario_id)
        object.__setattr__(self, "changed_by", changed_by)
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "timestamp", datetime.now())
        object.__setattr__(self, "event_type", "scenario.configuration.changed")
        object.__setattr__(self, "metadata", metadata or {})


class EventBus:
    """Simple synchronous event bus for domain events.

    Implemented as a Singleton via class methods — all callers share the same
    handler list. ``_handlers`` is intentionally a class-level variable so that
    ``register`` and ``publish`` work without an instance.
    """

    _handlers: ClassVar[list[Any]] = []

    @classmethod
    def register(cls, handler: Any) -> None:
        if handler not in cls._handlers:
            cls._handlers.append(handler)

    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        for handler in cls._handlers:
            if hasattr(handler, "handle"):  # pragma: no cover - partial branch
                handler.handle(event)


class EventLogger:
    """Audit trail logger for domain events."""

    def __init__(self, log_file: str | Path | None = None):
        self.log_file = Path(log_file) if log_file else None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventLogger):
            return NotImplemented
        return self.log_file == other.log_file

    def __hash__(self) -> int:
        return hash(self.log_file)

    def handle(self, event: DomainEvent) -> None:
        log_msg = f"[{event.timestamp.isoformat()}] {event.event_type.upper()}: {event}"
        # Always print to console
        print(log_msg)

        # Optionally log to file
        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_msg + "\n")
            except Exception as e:  # noqa: BLE001 — log writer must not crash the domain
                print(f"Error writing to log file: {e}")

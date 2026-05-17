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
Unit tests for domain events and event bus.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from fhs.core.model.events import (
    DomainEvent,
    EventBus,
    EventLogger,
    ScenarioConfigurationChanged,
)


class TestDomainEvent:
    """Tests for DomainEvent base class."""

    def test_domain_event_is_frozen(self):
        """Test that DomainEvent is immutable."""
        event = DomainEvent(
            timestamp=datetime.now(),
            event_type="test.event",
            metadata={"key": "value"},
        )

        with pytest.raises(Exception):  # dataclass frozen raises FrozenInstanceError
            event.event_type = "modified"


class TestScenarioConfigurationChanged:
    """Tests for ScenarioConfigurationChanged event."""

    def test_event_initialization(self):
        """Test event initialization with all fields."""
        event = ScenarioConfigurationChanged(
            scenario_id="blockchain",
            changed_by="test_user",
            changes={"budget": 100000},
        )

        assert event.scenario_id == "blockchain"
        assert event.changed_by == "test_user"
        assert event.changes == {"budget": 100000}
        assert event.event_type == "scenario.configuration.changed"
        assert isinstance(event.timestamp, datetime)

    def test_event_with_metadata(self):
        """Test event initialization with custom metadata."""
        custom_meta = {"source": "notebook", "version": "1.0"}
        event = ScenarioConfigurationChanged(
            scenario_id="test",
            changed_by="agent",
            changes={"features": []},
            metadata=custom_meta,
        )

        assert event.metadata == custom_meta


class TestEventBus:
    """Tests for EventBus."""

    @staticmethod
    def setup_method():
        """Clear handlers before each test."""
        EventBus._handlers.clear()

    def test_register_handler(self):
        """Test registering an event handler."""
        handler = MockHandler()
        EventBus.register(handler)

        assert handler in EventBus._handlers

    def test_register_same_handler_twice(self):
        """Test registering the same handler twice doesn't duplicate."""
        handler = MockHandler()
        EventBus.register(handler)
        EventBus.register(handler)

        assert EventBus._handlers.count(handler) == 1

    def test_publish_event_calls_handlers(self):
        """Test publishing event calls all registered handlers."""
        handler1 = MockHandler()
        handler2 = MockHandler()

        EventBus.register(handler1)
        EventBus.register(handler2)

        event = ScenarioConfigurationChanged(
            scenario_id="test", changed_by="user", changes={}
        )
        EventBus.publish(event)

        assert handler1.received_event == event
        assert handler2.received_event == event

    def test_publish_without_handlers(self):
        """Test publishing event without handlers doesn't raise."""
        event = ScenarioConfigurationChanged(
            scenario_id="test", changed_by="user", changes={}
        )
        EventBus.publish(event)  # Should not raise


class TestEventLogger:
    """Tests for EventLogger."""

    def test_logger_handles_event(self, capsys):
        """Test logger prints event to console."""
        logger = EventLogger()
        event = ScenarioConfigurationChanged(
            scenario_id="test", changed_by="user", changes={"budget": 50000}
        )

        logger.handle(event)

        captured = capsys.readouterr()
        assert "SCENARIO.CONFIGURATION.CHANGED" in captured.out
        assert "test" in captured.out

    def test_logger_writes_to_file(self):
        """Test logger writes event to log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = EventLogger(log_file=log_file)

            event = ScenarioConfigurationChanged(
                scenario_id="test", changed_by="user", changes={"budget": 50000}
            )

            logger.handle(event)

            assert log_file.exists()
            content = log_file.read_text()
            assert "SCENARIO.CONFIGURATION.CHANGED" in content
            assert "test" in content

    def test_logger_creates_directory_if_missing(self):
        """Test logger creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "subdir" / "test.log"
            logger = EventLogger(log_file=log_file)

            event = ScenarioConfigurationChanged(
                scenario_id="test", changed_by="user", changes={}
            )

            logger.handle(event)

            assert log_file.parent.exists()
            assert log_file.exists()

    def test_logger_handles_write_errors_gracefully(self, capsys):
        """Test logger handles write errors gracefully."""
        # Use a file path that will fail (e.g., read-only directory)
        log_file = Path("/dev/null/impossible.log")
        logger = EventLogger(log_file=log_file)

        event = ScenarioConfigurationChanged(
            scenario_id="test", changed_by="user", changes={}
        )

        # Should not raise, but print error
        logger.handle(event)

        captured = capsys.readouterr()
        # Should still print the event
        assert "SCENARIO.CONFIGURATION.CHANGED" in captured.out

    def test_logger_equality(self):
        """Test EventLogger equality comparison."""
        log1 = EventLogger(log_file=Path("/tmp/test.log"))
        log2 = EventLogger(log_file=Path("/tmp/test.log"))
        log3 = EventLogger(log_file=Path("/tmp/other.log"))

        assert log1 == log2
        assert log1 != log3

    def test_logger_equality_with_non_logger(self):
        """Test EventLogger equality with non-EventLogger returns NotImplemented."""
        logger = EventLogger()
        result = logger.__eq__("not a logger")
        assert result is NotImplemented

    def test_logger_hash(self):
        """Test EventLogger is hashable."""
        log1 = EventLogger(log_file=Path("/tmp/test.log"))
        log2 = EventLogger(log_file=Path("/tmp/test.log"))

        # Same log file should have same hash
        assert hash(log1) == hash(log2)

        # Can be added to set
        logger_set = {log1, log2}
        assert len(logger_set) == 1


class MockHandler:
    """Mock event handler for testing."""

    def __init__(self):
        self.received_event = None

    def handle(self, event: DomainEvent):
        self.received_event = event

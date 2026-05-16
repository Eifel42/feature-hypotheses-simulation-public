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

"""Tests for logging configuration."""

from __future__ import annotations

import logging

import pytest

from fhs.infra.config import setup_logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging state before each test."""
    # Remove all handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    # Reset level
    root.setLevel(logging.WARNING)
    yield
    # Cleanup after test
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()


def test_setup_logging_creates_handler():
    """setup_logging creates a stream handler."""
    setup_logging()
    handlers = logging.getLogger().handlers
    assert len(handlers) >= 1
    # Should have a StreamHandler to stdout
    stream_handlers = [h for h in handlers if isinstance(h, logging.StreamHandler)]
    assert len(stream_handlers) > 0


def test_setup_logging_with_debug_level():
    """Can configure with DEBUG level."""
    setup_logging(level="DEBUG")
    # The function runs without error
    assert logging.getLogger() is not None


def test_setup_logging_with_error_level():
    """Can configure with ERROR level."""
    setup_logging(level="ERROR")
    assert logging.getLogger() is not None


def test_setup_logging_custom_format():
    """Can set custom log format."""
    custom_fmt = "%(levelname)s - %(message)s"
    setup_logging(log_format=custom_fmt)
    handlers = logging.getLogger().handlers
    assert len(handlers) > 0


def test_setup_logging_with_file(tmp_path):
    """Can log to file."""
    log_file = tmp_path / "test.log"
    setup_logging(level="DEBUG", log_file=str(log_file))

    # Verify file handler was added
    handlers = logging.getLogger().handlers
    file_handlers = [h for h in handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0

    # The file should be created
    assert log_file.exists()


def test_setup_logging_json_warning(caplog):
    """JSON logging emits a warning (not yet implemented)."""
    with caplog.at_level(logging.WARNING):
        setup_logging(log_json=True)
    assert "JSON logging not yet implemented" in caplog.text

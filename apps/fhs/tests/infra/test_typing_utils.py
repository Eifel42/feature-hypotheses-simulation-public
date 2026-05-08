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

"""Tests for infra typing utilities (JSON/YAML loading)."""

from __future__ import annotations

import pytest
import yaml

from fhs.infra.typing_utils import safe_json_load, safe_yaml_load

# JSON loading tests


def test_safe_json_load_success(tmp_path):
    """Load a valid JSON object."""
    path = tmp_path / "data.json"
    path.write_text('{"key": "value", "num": 42}', encoding="utf-8")
    result = safe_json_load(path)
    assert result == {"key": "value", "num": 42}


def test_safe_json_load_rejects_list(tmp_path):
    """Reject JSON that is not an object."""
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="expected JSON object"):
        safe_json_load(path)


def test_safe_json_load_rejects_scalar(tmp_path):
    """Reject JSON scalar values."""
    path = tmp_path / "scalar.json"
    path.write_text('"just a string"', encoding="utf-8")
    with pytest.raises(ValueError, match="expected JSON object"):
        safe_json_load(path)


# ── YAML loading tests ────────────────────────────────────────────────────────


def test_safe_yaml_load_success(tmp_path):
    """Load a valid YAML mapping."""
    path = tmp_path / "data.yaml"
    path.write_text("key: value\nnum: 42\n", encoding="utf-8")
    result = safe_yaml_load(path, yaml.safe_load)
    assert result == {"key": "value", "num": 42}


def test_safe_yaml_load_rejects_list(tmp_path):
    """Reject YAML that is not a mapping."""
    path = tmp_path / "list.yaml"
    path.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected YAML mapping"):
        safe_yaml_load(path, yaml.safe_load)


def test_safe_yaml_load_rejects_scalar(tmp_path):
    """Reject YAML scalar values."""
    path = tmp_path / "scalar.yaml"
    path.write_text("just a string\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected YAML mapping"):
        safe_yaml_load(path, yaml.safe_load)

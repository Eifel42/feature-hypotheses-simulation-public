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

"""Tests for fhs.cli — load_features() and main() CLI entrypoint."""

import json
import os

import pytest
import yaml

from fhs.cli import load_features, main
from fhs.core.model import Feature

# ── Fixtures ────────────────────────────────────────────────────────────


def _features_data():
    return [
        {
            "name": "F1",
            "expected_users": 100,
            "conversion_rate": 0.5,
            "uncertainty": 0.2,
        },
        {
            "name": "F2",
            "expected_users": 200,
            "conversion_rate": 0.3,
            "uncertainty": 0.1,
        },
    ]


@pytest.fixture
def yaml_file(tmp_path):
    path = tmp_path / "features.yaml"
    yaml.dump({"features": _features_data()}, path.open("w"))
    return str(path)


@pytest.fixture
def yaml_file_list(tmp_path):
    """YAML with a bare list (no 'features' key)."""
    path = tmp_path / "features_list.yaml"
    yaml.dump(_features_data(), path.open("w"))
    return str(path)


@pytest.fixture
def json_file(tmp_path):
    path = tmp_path / "features.json"
    json.dump({"features": _features_data()}, path.open("w"))
    return str(path)


@pytest.fixture
def json_file_list(tmp_path):
    path = tmp_path / "features_list.json"
    json.dump(_features_data(), path.open("w"))
    return str(path)


@pytest.fixture
def csv_file(tmp_path):
    path = tmp_path / "features.csv"
    path.write_text(
        "name,expected_users,conversion_rate,uncertainty\n"
        "F1,100,0.5,0.2\n"
        "F2,200,0.3,0.1\n"
    )
    return str(path)


# ── load_features tests ────────────────────────────────────────────────


class TestLoadFeatures:
    def test_load_yaml(self, yaml_file):
        features = load_features(yaml_file)
        assert len(features) == 2
        assert all(isinstance(f, Feature) for f in features)
        assert features[0].name == "F1"

    def test_load_yaml_bare_list(self, yaml_file_list):
        features = load_features(yaml_file_list)
        assert len(features) == 2

    def test_load_json(self, json_file):
        features = load_features(json_file)
        assert len(features) == 2
        assert features[1].name == "F2"

    def test_load_json_bare_list(self, json_file_list):
        features = load_features(json_file_list)
        assert len(features) == 2

    def test_load_csv(self, csv_file):
        features = load_features(csv_file)
        assert len(features) == 2
        assert features[0].expected_users == 100

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "features.xml"
        path.write_text("<features/>")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_features(str(path))

    def test_yml_extension(self, tmp_path):
        path = tmp_path / "features.yml"
        yaml.dump(_features_data(), path.open("w"))
        features = load_features(str(path))
        assert len(features) == 2


# ── main() CLI tests ───────────────────────────────────────────────────


class TestMainCLI:
    def test_no_command_prints_help(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["fhs"])
        main()
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower() or "command" in captured.out.lower()

    def test_plan_command_stdout(self, monkeypatch, capsys, yaml_file):
        monkeypatch.setattr(
            "sys.argv",
            [
                "fhs",
                "plan",
                "--features",
                yaml_file,
                "--scenarios",
                "1000",
                "--seed",
                "42",
            ],
        )
        main()
        captured = capsys.readouterr()
        assert "F1" in captured.out or "F2" in captured.out

    def test_plan_command_output_file(self, monkeypatch, tmp_path, yaml_file):
        output = str(tmp_path / "report.md")
        monkeypatch.setattr(
            "sys.argv",
            [
                "fhs",
                "plan",
                "--features",
                yaml_file,
                "--scenarios",
                "1000",
                "--seed",
                "42",
                "--output",
                output,
            ],
        )
        main()
        assert os.path.exists(output)
        with open(output) as fh:
            content = fh.read()
        assert len(content) > 0

    def test_plan_invalid_file_exits(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            ["fhs", "plan", "--features", "/nonexistent/features.yaml"],
        )
        with pytest.raises(SystemExit):
            main()

    def test_plan_with_budget(self, monkeypatch, capsys, yaml_file):
        monkeypatch.setattr(
            "sys.argv",
            [
                "fhs",
                "plan",
                "--features",
                yaml_file,
                "--budget",
                "50000",
                "--scenarios",
                "1000",
                "--seed",
                "42",
            ],
        )
        main()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_plan_distribution_lognormal(self, monkeypatch, capsys, yaml_file):
        monkeypatch.setattr(
            "sys.argv",
            [
                "fhs",
                "plan",
                "--features",
                yaml_file,
                "--scenarios",
                "1000",
                "--seed",
                "42",
                "--distribution",
                "lognormal",
            ],
        )
        main()
        captured = capsys.readouterr()
        assert len(captured.out) > 0

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

from fhs.infra.versioning import VersioningService


def test_versioning_service_creates_snapshot(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    scenario_id = "test_scenario"
    config_data = {"id": scenario_id, "data": "value"}

    snapshot_path = service.create_snapshot(scenario_id, config_data)

    assert snapshot_path.exists()
    assert snapshot_path.parent == config_dir / "versions"
    assert snapshot_path.name.startswith(f"{scenario_id}_")
    assert snapshot_path.suffix == ".json"


def test_versioning_service_lists_versions(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    scenario_id = "test_scenario"
    service.create_snapshot(scenario_id, {"v": 1})
    # Wait a bit to ensure distinct timestamps
    import time

    time.sleep(1.1)
    service.create_snapshot(scenario_id, {"v": 2})

    versions = service.list_versions(scenario_id)

    # Check all files in versions dir
    import os

    print(f"Files in versions dir: {os.listdir(service.versions_dir)}")

    assert len(versions) == 2
    # Sorted newest first by default in our implementation
    assert versions[0]["timestamp"] >= versions[1]["timestamp"]


def test_versioning_service_restores_version(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    scenario_id = "test_scenario"
    config_data = {"v": 1, "nested": {"key": "val"}}
    snapshot_path = service.create_snapshot(scenario_id, config_data)

    restored = service.restore_version(scenario_id, snapshot_path.name)

    assert restored == config_data


def test_create_snapshot_stores_description(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    snapshot_path = service.create_snapshot(
        "blockchain", {"budget": 100_000}, description="Q1 baseline"
    )

    import json

    with open(snapshot_path) as f:
        data = json.load(f)

    assert data["_version_description"] == "Q1 baseline"


def test_list_versions_includes_description(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    service.create_snapshot("blockchain", {"v": 1}, description="Sprint 1")
    versions = service.list_versions("blockchain")

    assert len(versions) == 1
    assert versions[0]["description"] == "Sprint 1"


def test_list_versions_empty_description_when_not_set(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    service = VersioningService(config_dir)

    service.create_snapshot("blockchain", {"v": 1})
    versions = service.list_versions("blockchain")

    assert versions[0]["description"] == ""

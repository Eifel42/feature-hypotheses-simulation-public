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

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class VersioningService:
    """
    Service for managing scenario versions (snapshots).
    Provides backup and restore functionality for scenario configurations.
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.versions_dir = config_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(
        self,
        scenario_id: str,
        config_dict: dict,
        description: str = "",
    ) -> Path:
        """Create a timestamped snapshot of a scenario configuration.

        Parameters
        ----------
        scenario_id:
            The identifier of the scenario (e.g. ``"blockchain"``).
        config_dict:
            The current configuration as a dictionary.
        description:
            Optional human-readable label for the snapshot
            (e.g. ``"Q1 baseline"`` or ``"After budget cut"``).
            Stored in the snapshot JSON under ``"_version_description"``.

        Returns
        -------
        Path
            Path to the created snapshot file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_filename = f"{scenario_id}_{timestamp}.json"
        snapshot_path = self.versions_dir / snapshot_filename

        payload = dict(config_dict)
        if description:
            payload["_version_description"] = description

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return snapshot_path

    def list_versions(self, scenario_id: str) -> list[dict]:
        """
        List available versions for a scenario.

        Returns:
            List of version info dicts sorted by timestamp (newest first)
        """
        versions = []
        # Pattern: {scenario_id}_YYYYMMDD_HHMMSS.json
        for file in self.versions_dir.glob(f"{scenario_id}_*.json"):
            # Parse timestamp from filename - it's always the last 15 chars before .json
            # Format: YYYYMMDD_HHMMSS (8 + 1 + 6 = 15 chars)
            try:
                stem = file.stem
                if len(stem) < 16:  # scenario_id + _ + 15 chars
                    continue  # pragma: no cover - defensive

                ts_part = stem[-15:]
                # Try parsing the specific format YYYYMMDD_HHMMSS
                try:
                    dt = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
                except ValueError:  # pragma: no cover - optional dep
                    continue  # pragma: no cover - optional dep

                # Read description from snapshot payload if present
                description = ""
                try:
                    with open(file, encoding="utf-8") as fh:
                        snapshot = json.load(fh)
                    description = snapshot.get("_version_description", "")
                except (
                    OSError,
                    ValueError,
                    KeyError,
                ):  # pragma: no cover - optional dep
                    pass  # pragma: no cover - optional dep

                versions.append(
                    {
                        "scenario_id": scenario_id,
                        "timestamp": dt.isoformat(),
                        "filename": file.name,
                        "path": file,
                        "description": description,
                    }
                )
            except (ValueError, IndexError):  # pragma: no cover - optional dep
                continue  # pragma: no cover - optional dep

        return sorted(versions, key=lambda x: x["timestamp"], reverse=True)

    def restore_version(self, _scenario_id: str, filename: str) -> dict[str, Any]:
        """
        Load a specific version of a scenario.

        Args:
            _scenario_id: The identifier of the scenario (unused, kept for API compatibility)
            filename: The version filename to restore

        Returns:
            The loaded configuration dictionary
        """
        version_path = self.versions_dir / filename
        if not version_path.exists():
            raise FileNotFoundError(
                f"Version file {filename} not found"
            )  # pragma: no cover - defensive

        with open(version_path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(
                f"Version file {filename} does not contain a JSON object"
            )  # pragma: no cover - defensive
        return data

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2025 eifel42.dev
"""
Architecture contract: all version references must point to Python 3.14.

Scans pyproject.toml files, CI workflow YAML, and Dockerfiles for any
reference to 3.11, 3.12, or 3.13 — old version pins that must not exist.
"""

from __future__ import annotations

import re
from pathlib import Path


def _find_repo_root() -> Path:
    """Locate project root for both monorepo and container test layouts."""
    current = Path(__file__).resolve()
    for candidate in [current.parent, *current.parents]:
        if (candidate / "apps" / "fhs" / "config" / "pyproject.toml").is_file():
            return candidate
        if (candidate / "config" / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("Could not detect repository root from test location")


REPO_ROOT = _find_repo_root()

# Patterns that indicate an old Python version reference (not in .venv or comments)
_OLD_VERSION_RE = re.compile(r"python.*3\.(11|12|13)", re.IGNORECASE)

# Files and globs to scan
_SCAN_GLOBS = [
    "pyproject.toml",
    "config/pyproject.toml",
    "apps/fhs/pyproject.toml",
    "apps/fhs/config/pyproject.toml",
    ".github/workflows/*.yml",
    ".github/workflows/*.yaml",
    "cicd/docker-compose.yml",
    "cicd/docker/*.yml",
    "cicd/containers/Dockerfile*",
    "cicd/docker/Dockerfile*",
]

# Patterns explicitly allowed (third-party comments, historical notes)
_ALLOWLIST_RE = re.compile(
    r"(#.*3\.(11|12|13))"  # comment lines
    r"|(CHANGELOG|HISTORY|RELEASE|NOTICE)"  # history files
)


def _collect_files() -> list[Path]:
    files: list[Path] = []
    for pattern in _SCAN_GLOBS:
        files.extend(REPO_ROOT.glob(pattern))
    return files


def test_all_version_refs_are_3_14() -> None:
    """No project-owned file pins Python 3.11, 3.12, or 3.13."""
    violations: list[str] = []

    for path in _collect_files():
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _OLD_VERSION_RE.search(line) and not _ALLOWLIST_RE.search(line):
                rel = path.relative_to(REPO_ROOT)
                violations.append(f"{rel}:{lineno}: {line.strip()}")

    if violations:
        details = "\n".join(f"  - {v}" for v in violations)
        assert False, (
            "Found old Python version references (must all be 3.14):\n" + details
        )

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
Architecture contracts for DDD-style boundaries.

This is the Python equivalent of ArchUnit-style dependency rules with
"freeze" support for known legacy violations.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "fhs"
PROJECT_ROOT = SRC_ROOT.parent.parent


# Forbidden target layers per source layer.
LAYER_RULES: dict[str, set[str]] = {
    "domain_model": {"domain_service", "application", "infrastructure", "presentation"},
    "domain_service": {"application", "infrastructure", "presentation"},
    "application": {"presentation"},
    "infrastructure": {"application", "presentation"},
    "presentation": {"domain_service", "infrastructure"},
}


# Freeze list: existing violations allowed for now.
# New violations fail the build immediately.
#
# Phase 2 Complete (2026-03-10): 8/9 violations resolved! 🎉
# Phase 5 Complete (2026-03-10): 9/9 violations resolved! 🎉🎉🎉
# - Moved SimulationConfig from infra.config to core.model (7 violations) ✅
# - ScenarioService.create_default() factory method (1 violation) ✅
# - Removed deprecated simulator.plot_*() methods (1 violation) ✅
#
# 🏆 100% CLEAN ARCHITECTURE - Zero violations!
KNOWN_VIOLATIONS: set[tuple[str, str]] = set()


@dataclass(frozen=True, order=True)
class ImportViolation:
    source_module: str
    target_module: str
    source_layer: str
    target_layer: str
    source_file: Path
    lineno: int


def classify_layer(module_name: str) -> str | None:
    if module_name.startswith("fhs.core.model"):
        return "domain_model"
    if module_name.startswith("fhs.core.services"):
        return "domain_service"
    if module_name.startswith("fhs.application"):
        return "application"
    if module_name.startswith("fhs.infra"):
        return "infrastructure"
    if module_name.startswith(("fhs.presentation", "fhs.notebook", "fhs.plotting")):
        return "presentation"
    return None


def iter_python_files() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if "__pycache__" not in p.parts)


def module_name_from_path(path: Path) -> str:
    relative = path.relative_to(SRC_ROOT).with_suffix("")
    return "fhs." + ".".join(relative.parts)


def resolve_relative_import(current_module: str, level: int, module: str | None) -> str:
    parts = current_module.split(".")
    anchor = parts[:-level]
    if module:
        anchor.extend(module.split("."))
    return ".".join(anchor)


def iter_imports(tree: ast.AST, source_module: str) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                imported_module = resolve_relative_import(
                    source_module,
                    node.level,
                    node.module,
                )
            else:
                imported_module = node.module or ""
            if imported_module:
                imports.append((imported_module, node.lineno))
    return imports


def collect_layer_violations() -> list[ImportViolation]:
    violations: dict[tuple[str, str], ImportViolation] = {}

    for source_file in iter_python_files():
        source_module = module_name_from_path(source_file)
        source_layer = classify_layer(source_module)
        if source_layer is None:
            continue

        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for target_module, lineno in iter_imports(tree, source_module):
            target_layer = classify_layer(target_module)
            if target_layer not in LAYER_RULES.get(source_layer, set()):
                continue

            key = (source_module, target_module)
            previous = violations.get(key)
            if previous is None or lineno < previous.lineno:
                violations[key] = ImportViolation(
                    source_module=source_module,
                    target_module=target_module,
                    source_layer=source_layer,
                    target_layer=target_layer,
                    source_file=source_file,
                    lineno=lineno,
                )

    return sorted(violations.values())


def _format_violation(violation: ImportViolation) -> str:
    relative = violation.source_file.relative_to(PROJECT_ROOT)
    return (
        f"{violation.source_module} -> {violation.target_module} "
        f"[{violation.source_layer}->{violation.target_layer}] "
        f"({relative}:{violation.lineno})"
    )


def test_ddd_architecture_rules_no_new_violations() -> None:
    violations = collect_layer_violations()
    found_pairs = {(v.source_module, v.target_module) for v in violations}
    violation_by_pair = {(v.source_module, v.target_module): v for v in violations}

    new_violations = sorted(found_pairs - KNOWN_VIOLATIONS)
    resolved_violations = sorted(KNOWN_VIOLATIONS - found_pairs)

    if new_violations or resolved_violations:
        lines = [
            "DDD architecture contract mismatch.",
            "",
            "Status:",
            f"- found={len(found_pairs)}",
            f"- frozen={len(KNOWN_VIOLATIONS)}",
        ]

        if new_violations:
            lines.append("")
            lines.append("New violations (must be fixed or explicitly frozen):")
            for pair in new_violations:
                lines.append(f"- {_format_violation(violation_by_pair[pair])}")

        if resolved_violations:
            lines.append("")
            lines.append("Resolved frozen violations (remove from KNOWN_VIOLATIONS):")
            for source_module, target_module in resolved_violations:
                lines.append(f"- {source_module} -> {target_module}")

        assert False, "\n".join(lines)


def test_domain_model_remains_pure() -> None:
    violations = [
        violation
        for violation in collect_layer_violations()
        if violation.source_layer == "domain_model"
    ]
    if violations:
        details = "\n".join(f"- {_format_violation(v)}" for v in violations)
        assert False, "Domain model must not depend on outer layers:\n" + details


def test_repository_contract_defined_as_protocol() -> None:
    """jMolecules-like contract: repository types live as domain protocols."""
    repo_file = SRC_ROOT / "core" / "model" / "repositories.py"
    tree = ast.parse(repo_file.read_text(encoding="utf-8"))

    protocol_classes = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                protocol_classes.append(node.name)
            if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                protocol_classes.append(node.name)

    assert protocol_classes, (
        "Expected at least one repository contract based on typing.Protocol "
        f"in {repo_file}."
    )

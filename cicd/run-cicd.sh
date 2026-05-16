#!/bin/bash
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

# Local-first CI/CD and quality script.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LIMA_VM="${LIMA_VM:-fhs}"
DOCKER=(env LIMA_VM="$LIMA_VM" bash "$ROOT_DIR/cicd/docker-lima.sh")

COMMAND=${1:-help}
COMPOSE_FILE="$ROOT_DIR/cicd/docker-compose.yml"
ENV_FILE="$ROOT_DIR/cicd/.env.example"
QUALITY_DIR="$ROOT_DIR/build-output/quality"
MIN_COVERAGE_RATE="0.95"
MIN_COVERAGE_PERCENT="95.0%"

if [ -f "$ROOT_DIR/cicd/.env.local" ]; then
    ENV_FILE="$ROOT_DIR/cicd/.env.local"
fi

# Preserve explicit shell overrides before loading ENV_FILE.
SONAR_HOST_URL_WAS_SET="${SONAR_HOST_URL+x}"
SONAR_TOKEN_WAS_SET="${SONAR_TOKEN+x}"
ORIGINAL_SONAR_HOST_URL="${SONAR_HOST_URL-}"
ORIGINAL_SONAR_TOKEN="${SONAR_TOKEN-}"

# Load selected env file so script-level variables (for example SONAR_HOST_URL and
# SONAR_TOKEN) are available outside docker-compose as well.
if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

if [ -n "$SONAR_HOST_URL_WAS_SET" ]; then
    SONAR_HOST_URL="$ORIGINAL_SONAR_HOST_URL"
fi
if [ -n "$SONAR_TOKEN_WAS_SET" ]; then
    SONAR_TOKEN="$ORIGINAL_SONAR_TOKEN"
fi

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker_compose() {
    JUPYTER_TOKEN="${JUPYTER_TOKEN:-sonar-placeholder-token}" \
        "${DOCKER[@]}" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

is_local_sonar_host() {
    case "${SONAR_HOST_URL:-}" in
        http://localhost*|https://localhost*|http://127.0.0.1*|https://127.0.0.1*|http://0.0.0.0*|https://0.0.0.0*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

resolve_project_version() {
    python3 - \
        "$ROOT_DIR/apps/fhs/pyproject.toml" \
        "$ROOT_DIR/apps/fhs/src/fhs/__init__.py" <<'PY'
import ast
import re
import sys
import tomllib
from pathlib import Path

pyproject_path = Path(sys.argv[1])
init_path = Path(sys.argv[2])

project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
project_version = project.get("project", {}).get("version")
if not isinstance(project_version, str) or not project_version:
    raise SystemExit(f"Missing project.version in {pyproject_path}")

if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", project_version):
    raise SystemExit(f"Invalid project.version in {pyproject_path}: {project_version}")

init_tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
package_version = None
for node in init_tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__version__":
                package_version = ast.literal_eval(node.value)

if package_version != project_version:
    raise SystemExit(
        "Version mismatch: "
        f"{pyproject_path} has {project_version}, "
        f"{init_path} has {package_version!r}"
    )

print(project_version)
PY
}

generate_coverage_report() {
    log_info "Running pytest with coverage..."
    mkdir -p "$QUALITY_DIR"
    mkdir -p "$ROOT_DIR/build-output/test-results"

    local raw="$ROOT_DIR/apps/fhs/coverage.xml"
    local out="$QUALITY_DIR/coverage.xml"
    local raw_junit="$ROOT_DIR/apps/fhs/junit-quality.xml"
    local out_junit="$ROOT_DIR/build-output/test-results/junit-quality.xml"

    # Drop any stale report so a pytest failure cannot be masked by an old
    # file lingering from a previous run.
    rm -f "$raw" "$out" "$raw_junit" "$out_junit"
    find "$ROOT_DIR" "$ROOT_DIR/apps/fhs" -maxdepth 1 -type f \
        \( -name ".coverage" -o -name ".coverage.*" \) -delete

    # Architecture tests scan repo-wide files and need the full repository
    # checkout, but the fhs-dev container only mounts apps/fhs. They carry no
    # coverage signal for src/fhs and are covered by `./cicd/run-cicd.sh arch`.
    if ! docker_compose --profile dev run --rm fhs-dev \
        bash -lc '
        python -m coverage erase &&
        python -m pytest tests/ \
            --ignore=tests/architecture \
            --cov=src/fhs \
            --cov-branch \
            --cov-report=xml:/workspace/coverage.xml \
            --cov-report=term \
            --cov-fail-under=95 \
            --junitxml=/workspace/junit-quality.xml \
            --tb=short \
            -q
        '; then
        log_error "pytest failed; aborting quality run (no coverage report transmitted)"
        return 1
    fi

    if [ ! -f "$raw" ]; then
        log_error "Expected coverage report at $raw but it was not produced"
        return 1
    fi
    if [ ! -f "$raw_junit" ]; then
        log_error "Expected JUnit report at $raw_junit but it was not produced"
        return 1
    fi

    rewrite_coverage_for_repo_root "$raw" "$out"
    cp "$raw_junit" "$out_junit"
    validate_sonar_reports "$out" "$out_junit"
    log_success "Coverage report ready at $out"
    log_success "JUnit report ready at $out_junit"
}

rewrite_coverage_for_repo_root() {
    local raw_report="$1"
    local out_report="$2"

    python3 - "$ROOT_DIR" "$raw_report" "$out_report" <<'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root_dir = Path(sys.argv[1])
raw_report = Path(sys.argv[2])
out_report = Path(sys.argv[3])
package_root = Path("apps/fhs/src/fhs")

tree = ET.parse(raw_report)
root = tree.getroot()

for source_node in root.findall(".//source"):
    source_node.text = "."

for class_node in root.findall(".//class"):
    filename = Path(class_node.attrib["filename"])
    if filename.is_absolute():
        try:
            filename = filename.relative_to("/workspace/src/fhs")
        except ValueError as exc:
            raise SystemExit(
                f"Unexpected absolute coverage path: {class_node.attrib['filename']}"
            ) from exc

    if not str(filename).startswith(str(package_root)):
        filename = package_root / filename

    resolved = root_dir / filename
    if not resolved.is_file():
        raise SystemExit(f"Coverage path does not exist: {filename}")

    class_node.attrib["filename"] = filename.as_posix()

tree.write(out_report, encoding="utf-8", xml_declaration=True)
PY
}

validate_sonar_reports() {
    local coverage_report="$1"
    local junit_report="$2"

    log_info "Validating Sonar report paths..."
    python3 - \
        "$ROOT_DIR" \
        "$coverage_report" \
        "$junit_report" \
        "$MIN_COVERAGE_RATE" \
        "$MIN_COVERAGE_PERCENT" <<'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root_dir = Path(sys.argv[1])
coverage_report = Path(sys.argv[2])
junit_report = Path(sys.argv[3])
min_coverage_rate = float(sys.argv[4])
min_coverage_percent = sys.argv[5]

coverage_root = ET.parse(coverage_report).getroot()
classes = coverage_root.findall(".//class")
filenames = [class_node.attrib["filename"] for class_node in classes]

if not filenames:
    raise SystemExit(f"{coverage_report} does not contain any coverage classes")

invalid = [name for name in filenames if Path(name).is_absolute()]
if invalid:
    raise SystemExit(
        f"{coverage_report} contains absolute paths; first invalid path: {invalid[0]}"
    )

missing = [name for name in filenames if not (root_dir / name).is_file()]
if missing:
    preview = ", ".join(missing[:5])
    raise SystemExit(
        f"{coverage_report} contains paths Sonar cannot match from repo root: {preview}"
    )

line_rate = float(coverage_root.attrib.get("line-rate", "0"))
if line_rate <= 0:
    raise SystemExit(f"{coverage_report} has no measured line coverage")

branch_rate = float(coverage_root.attrib.get("branch-rate", "0"))
if branch_rate <= 0:
    raise SystemExit(f"{coverage_report} has no measured condition coverage")

if line_rate < min_coverage_rate:
    raise SystemExit(
        f"Line coverage gate failed: {line_rate:.1%} < {min_coverage_percent}"
    )
if branch_rate < min_coverage_rate:
    raise SystemExit(
        f"Condition coverage gate failed: {branch_rate:.1%} < {min_coverage_percent}"
    )

junit_root = ET.parse(junit_report).getroot()
tests = int(junit_root.attrib.get("tests", "0"))
if tests <= 0:
    tests = sum(int(node.attrib.get("tests", "0")) for node in junit_root.findall(".//testsuite"))
if tests <= 0:
    raise SystemExit(f"{junit_report} does not contain executed tests")

print(
    "Validated "
    f"{len(filenames)} coverage files, "
    f"{line_rate:.1%} line coverage, "
    f"{branch_rate:.1%} condition coverage, "
    f"{tests} tests"
)
PY
}

run_sonar_scan() {
    if [ -z "${SONAR_HOST_URL:-}" ]; then
        log_error "SONAR_HOST_URL is missing. Set it to the external SonarQube host (e.g. http://inoatec-nas:9000) in cicd/.env.local or the environment."
        return 1
    fi
    if is_local_sonar_host; then
        log_error "SONAR_HOST_URL points to a local host (${SONAR_HOST_URL}). This project only supports an external SonarQube server."
        return 1
    fi
    if [ -z "${SONAR_TOKEN:-}" ]; then
        log_error "SONAR_TOKEN is missing. Set it in cicd/.env.local or the environment."
        log_info "Example: SONAR_TOKEN=*** ./cicd/run-cicd.sh quality"
        return 1
    fi

    generate_coverage_report || return 1

    local project_version
    project_version="$(resolve_project_version)"

    mkdir -p "$QUALITY_DIR/sonar/cache"

    log_info "Running SonarScanner against external ${SONAR_HOST_URL} for version ${project_version} ..."
    if command -v sonar-scanner >/dev/null 2>&1; then
        log_info "Using local sonar-scanner executable"
        SONAR_SCANNER_JAVA_OPTS="${SONAR_SCANNER_JAVA_OPTS:--Xmx1024m}" \
            sonar-scanner \
            -Dsonar.host.url="$SONAR_HOST_URL" \
            -Dsonar.token="$SONAR_TOKEN" \
            -Dsonar.projectVersion="$project_version"

        log_success "Sonar scan completed"
        return 0
    fi

    log_info "Local sonar-scanner not found; using Docker image"
    "${DOCKER[@]}" run --rm \
        --platform "${SONAR_SCANNER_PLATFORM:-linux/amd64}" \
        -e SONAR_HOST_URL="$SONAR_HOST_URL" \
        -e SONAR_TOKEN="$SONAR_TOKEN" \
        -e SONAR_SCANNER_JAVA_OPTS="${SONAR_SCANNER_JAVA_OPTS:--Xmx1024m}" \
        -v "$ROOT_DIR:/usr/src" \
        -v "$QUALITY_DIR/sonar/cache:/opt/sonar-scanner/.sonar/cache" \
        -w /usr/src \
        sonarsource/sonar-scanner-cli:latest \
        -Dsonar.projectVersion="$project_version"

    log_success "Sonar scan completed"
}

cd "$ROOT_DIR"

case $COMMAND in
    arch)
        log_info "Running architecture tests..."
        docker_compose --profile dev run --rm fhs-dev \
            python -m pytest tests/architecture/ -v
        log_success "Architecture tests completed"
        ;;
    test)
        log_info "Running Python tests..."
        mkdir -p build-output/test-results
        docker_compose --profile dev run --rm fhs-dev \
            python -m pytest tests/ -v \
            --junitxml=/workspace/build-output/test-results/junit.xml \
            --tb=short
        log_success "Tests completed (results: build-output/test-results/junit.xml)"
        ;;
    lint)
        log_info "Running code quality checks..."
        docker_compose --profile dev run --rm fhs-dev bash -c "
            ruff format --check src/ tests/ &&
            ruff check src/ tests/
        "
        log_success "Code quality checks completed"
        ;;
    types)
        log_info "Running type checking..."
        docker_compose --profile dev run --rm fhs-dev \
            mypy --config-file config/pyproject.toml \
                --disable-error-code arg-type \
                --disable-error-code call-overload \
                --disable-error-code no-any-return \
                --disable-error-code attr-defined \
                --disable-error-code override \
                src/
        log_success "Type checking completed"
        ;;
    docs)
        log_info "Building documentation..."
        python3 scripts/check_docs_language.py
        docker_compose --profile docs run --rm docs-builder
        log_success "Documentation build completed"
        ;;
    docs-language)
        log_info "Running documentation language drift check..."
        python3 scripts/check_docs_language.py
        log_success "Documentation language drift check completed"
        ;;
    sbom)
        log_info "Generating SBOM..."
        docker_compose --profile dev run --rm fhs-dev bash -c "
            mkdir -p /workspace/build-output/sbom &&
            cyclonedx-py environment --output-format json --output-file build-output/sbom/sbom-requirements.json
        "
        log_success "SBOM generation completed"
        ;;
    audit)
        log_info "Running pip-audit against installed dependencies..."
        mkdir -p build-output/audit
        docker_compose --profile dev run --rm fhs-dev bash -c "
            pip-audit --format json --output build-output/audit/pip-audit.json
            pip-audit
        "
        log_success "Audit completed (report: build-output/audit/pip-audit.json)"
        ;;
    delivery-benchmark)
        LEVELS=${DELIVERY_BENCHMARK_LEVELS:-1000000}
        OUTPUT=${DELIVERY_BENCHMARK_OUTPUT:-tests/spikes/results/delivery_risk_scaling.json}
        TARGET_SCENARIOS=${DELIVERY_BENCHMARK_TARGET_SCENARIOS:-1000000}

        log_info "Running delivery-risk benchmark in Docker (levels=${LEVELS})..."
        docker_compose --profile dev run --rm \
            -e DELIVERY_BENCHMARK_LEVELS="$LEVELS" \
            -e DELIVERY_BENCHMARK_OUTPUT="$OUTPUT" \
            fhs-dev bash -lc '
                set -euo pipefail
                python3 tests/spikes/delivery_risk_scaling_harness.py \
                    --levels "$DELIVERY_BENCHMARK_LEVELS" \
                    --output "$DELIVERY_BENCHMARK_OUTPUT"
            '

        log_info "Validating benchmark output for scenarios=${TARGET_SCENARIOS}..."
        docker_compose --profile dev run --rm \
            -e DELIVERY_BENCHMARK_OUTPUT="$OUTPUT" \
            -e DELIVERY_BENCHMARK_TARGET_SCENARIOS="$TARGET_SCENARIOS" \
            fhs-dev bash -lc '
                set -euo pipefail
                python3 - <<"PY"
import json
import os
from pathlib import Path

output_path = Path(os.environ["DELIVERY_BENCHMARK_OUTPUT"])
target = int(os.environ["DELIVERY_BENCHMARK_TARGET_SCENARIOS"])

payload = json.loads(output_path.read_text(encoding="utf-8"))
measurements = payload.get("measurements", [])
match = next((m for m in measurements if int(m.get("scenarios", 0)) == target), None)
if match is None:
    raise SystemExit(f"No measurement found for scenarios={target} in {output_path}")
sample_count = int(match.get("sample_count_per_feature", 0))
runtime_seconds = match.get("runtime_seconds")
peak_python_heap_mib = match.get("peak_python_heap_mib")
if sample_count != target:
    raise SystemExit(
        "sample_count_per_feature mismatch: "
        f"expected {target}, got {sample_count}"
    )
print(
    "Validated delivery benchmark: "
    f"scenarios={target}, runtime={runtime_seconds}s, "
    f"peak_python_heap_mib={peak_python_heap_mib}"
)
PY
            '

        log_success "Delivery benchmark completed and validated"
        ;;
    security)
        log_info "Running security policy checks..."
        ./scripts/check-sandbox-security.sh
        log_success "Security policy checks completed"
        ;;
    quality-report|sonar-report)
        generate_coverage_report
        ;;
    quality|sonar)
        run_sonar_scan
        ;;
    pipeline)
        log_info "Running complete CI/CD pipeline..."
        $0 security && $0 arch && $0 test && $0 lint && $0 types && $0 sbom && $0 docs
        log_success "Pipeline completed"
        ;;
    ci)
        log_info "Running CI test suite (all validations)..."
        mkdir -p build-output/test-results
        docker_compose --profile ci run --rm fhs-test
        log_success "CI test suite completed"
        ;;
    dev)
        log_info "Starting development environment..."
        docker_compose --profile dev run --rm fhs-dev bash
        ;;
    clean)
        log_info "Cleaning up Docker resources..."
        docker_compose down --remove-orphans --rmi local
        log_success "Cleanup completed"
        ;;
    help|*)
        echo "FHS Local CI/CD Script"
        echo "======================"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  arch         - Run architecture tests (layer boundaries)"
        echo "  test         - Run Python tests (JUnit XML → build-output/)"
        echo "  lint         - Run code quality checks (ruff format + ruff check)"
        echo "  types        - Run type checking (mypy)"
        echo "  docs         - Build documentation"
        echo "  docs-language - Run documentation language drift check"
        echo "  sbom         - Generate SBOM"
        echo "  audit        - Scan installed dependencies for known vulnerabilities (pip-audit)"
        echo "  delivery-benchmark - Run 1M delivery benchmark in Docker"
        echo "  security     - Validate sandbox and Jupyter security defaults"
        echo "  quality-report - Generate and validate Sonar coverage/test reports without uploading"
        echo "  quality      - Run pytest with coverage and SonarScanner against the external SonarQube host"
        echo "  ci           - Run all validations (architecture + tests + lint + types)"
        echo "  pipeline     - Run complete pipeline (security + ci + sbom + docs)"
        echo "  dev          - Start development environment"
        echo "  clean        - Clean up Docker resources"
        echo ""
        echo "Examples:"
        echo "  $0 arch              # Run architecture tests only"
        echo "  $0 test              # Run unit tests only"
        echo "  $0 lint              # Run code quality checks only"
        echo "  $0 types             # Run type checking only"
        echo "  $0 docs-language     # Run documentation language drift check only"
        echo "  $0 delivery-benchmark # Run 1M delivery benchmark in Docker"
        echo "  $0 quality-report    # Validate reports before a Sonar upload"
        echo "  $0 quality           # Scan the repository against the external SonarQube"
        echo "  $0 ci                # Run all tests and validations"
        echo "  $0 pipeline          # Run complete CI/CD pipeline"
        echo "  $0 dev               # Start interactive development shell"
        ;;
esac

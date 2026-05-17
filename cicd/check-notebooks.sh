#!/usr/bin/env bash
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

# check-notebooks.sh — Execute all notebooks and fail if any notebook errors.
#
# Usage (inside container):
#   bash /workspace/cicd/check-notebooks.sh
#
# Exit codes:
#   0  All notebooks executed successfully
#   1  One or more notebooks failed to execute

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if [ -n "${NOTEBOOK_DIR:-}" ]; then
    NOTEBOOK_DIR="$NOTEBOOK_DIR"
elif [ -d "/workspace/notebooks" ]; then
    NOTEBOOK_DIR="/workspace/notebooks"
else
    NOTEBOOK_DIR="$REPO_ROOT/apps/fhs/notebooks"
fi

if command -v jupyter >/dev/null 2>&1; then
    JUPYTER_CMD=(jupyter)
else
    JUPYTER_CMD=(python3 -m jupyter)
fi

TIMEOUT="${NOTEBOOK_TIMEOUT:-300}"   # seconds per notebook

# Collect notebooks (skip checkpoints)
NOTEBOOKS=()
while IFS= read -r notebook; do
    NOTEBOOKS+=("$notebook")
done < <(
    find "$NOTEBOOK_DIR" \
        -name "*.ipynb" \
        -not -path "*/.ipynb_checkpoints/*" \
        | sort
)

if [ ${#NOTEBOOKS[@]} -eq 0 ]; then
    echo "ERROR: No notebooks found in $NOTEBOOK_DIR" >&2
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Notebook Compilation Check"
echo " Found ${#NOTEBOOKS[@]} notebooks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

FAILED=()
PASSED=()

for NB in "${NOTEBOOKS[@]}"; do
    REL="${NB#$NOTEBOOK_DIR/}"
    printf "  %-55s" "$REL"

    # Execute notebook into a throwaway directory so the source .ipynb stays
    # untouched (no execution_count / output-cell churn in `git status` after
    # `make up`). Failure surfaces via nbconvert's exit code as before.
    if "${JUPYTER_CMD[@]}" nbconvert \
        --to notebook \
        --execute \
        --output-dir /tmp/nb-check \
        --ExecutePreprocessor.timeout="$TIMEOUT" \
        --ExecutePreprocessor.kernel_name=python3 \
        "$NB" \
        > /tmp/nbconvert-out.txt 2>&1; then
        echo "✓"
        PASSED+=("$REL")
    else
        echo "✗  FAILED"
        FAILED+=("$REL")
        echo ""
        echo "    ── nbconvert output ──────────────────────────"
        grep -v "^$" /tmp/nbconvert-out.txt | head -30 | sed 's/^/    /'
        echo "    ──────────────────────────────────────────────"
        echo ""
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Results: ${#PASSED[@]} passed, ${#FAILED[@]} failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "Failed notebooks:"
    for NB in "${FAILED[@]}"; do
        echo "  ✗  $NB"
    done
    echo ""
    exit 1
fi

echo ""
echo "All notebooks compiled successfully."
echo ""

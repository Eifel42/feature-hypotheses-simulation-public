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

# docker-lima.sh — Transparent Docker wrapper for Lima VM environments.
#
# Tries host Docker first (DOCKER_HOST= to use OS default socket).
# If unreachable, starts the Lima VM and routes the command into it,
# so `make build` / `make up` / … work from the Mac without any manual
# `limactl shell` dance.
#
# Usage (set in Makefile):
#   DOCKER := bash cicd/docker-lima.sh

set -euo pipefail

LIMA_VM="${LIMA_VM:-fhs}"

# --------------------------------------------------------------------------
# 1. Try host Docker
# --------------------------------------------------------------------------
if DOCKER_HOST= docker info >/dev/null 2>&1; then
    exec env DOCKER_HOST= docker "$@"
fi

# --------------------------------------------------------------------------
# 2. Host Docker not reachable — ensure Lima VM is running
# --------------------------------------------------------------------------
if limactl list 2>/dev/null | grep -E "^${LIMA_VM}\s" | grep -q "Stopped"; then
    echo "Starting Lima VM '${LIMA_VM}'…" >&2
    limactl start "${LIMA_VM}" 2>&1 | grep -v "^$" >&2 || true
elif ! limactl list 2>/dev/null | grep -E "^${LIMA_VM}\s" | grep -q "Running"; then
    echo "Starting Lima VM '${LIMA_VM}'…" >&2
    limactl start "${LIMA_VM}" 2>&1 | grep -v "^$" >&2 || true
fi

# --------------------------------------------------------------------------
# 3. Build a shell-safe argument string and run inside the VM
# --------------------------------------------------------------------------
ARGS=()
for arg in "$@"; do
    ARGS+=("$(printf '%q' "$arg")")
done

WORKDIR="$(pwd)"

exec limactl shell "${LIMA_VM}" -- bash -c \
    "cd $(printf '%q' "${WORKDIR}") && DOCKER_HOST= docker ${ARGS[*]}"

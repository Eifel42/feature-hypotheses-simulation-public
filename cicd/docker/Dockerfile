# syntax=docker/dockerfile:1.4

# ==============================================================================
# Unified Dockerfile for FHS Project
# ==============================================================================
# Multi-stage build with targets:
# - base: Shared Python + Java foundation
# - fhs: FHS development and Jupyter
# - docs: Documentation builder
# ==============================================================================

# ========================================
# Stage: Base - Shared Foundation
# ========================================
FROM --platform=$BUILDPLATFORM python:3.14-slim-bookworm AS base

# Install common runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /workspace

# ========================================
# Stage: FHS Builder - Scientific Python
# ========================================
FROM base AS fhs-builder

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY apps/fhs/config/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir pytest-xdist cyclonedx-bom

# Install FHS package
WORKDIR /tmp/fhs
COPY apps/fhs/config/pyproject.toml pyproject.toml
COPY apps/fhs/src/ src/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -e ".[notebooks]"

# ========================================
# Stage: FHS Runtime - Jupyter & Tests
# ========================================
FROM base AS fhs

LABEL maintainer="eifel42.dev"
LABEL description="FHS Development Environment with Jupyter Lab"
LABEL version="0.3.0"

# Install Liberation Sans for chart rendering (Apache 2.0 licence)
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash -u 1000 fhsuser && \
    mkdir -p /home/fhsuser/.jupyter /home/fhsuser/.cache && \
    chown -R fhsuser:fhsuser /home/fhsuser

# Copy Python packages from builder
COPY --from=fhs-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=fhs-builder /usr/local/bin /usr/local/bin
COPY --from=fhs-builder /usr/local/share/jupyter /usr/local/share/jupyter

# Copy application code
COPY --chown=fhsuser:fhsuser apps/fhs/src/ src/
COPY --chown=fhsuser:fhsuser apps/fhs/notebooks/ notebooks/
COPY --chown=fhsuser:fhsuser apps/fhs/tests/ tests/
COPY --chown=fhsuser:fhsuser apps/fhs/config/ config/

# Set FHS-specific environment
ENV PYTHONPATH="/workspace/src" \
    OPENBLAS_NUM_THREADS=12 \
    OMP_NUM_THREADS=12 \
    MALLOC_ARENA_MAX=4

EXPOSE 8888

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8888/ || exit 1

USER fhsuser

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]

# ========================================
# Stage: Docs Builder - Java + docToolchain
# ========================================
FROM base AS docs-builder

# Install Java and tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    graphviz \
    unzip \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

# Install PlantUML
RUN --mount=type=cache,target=/tmp/downloads \
    curl -L https://github.com/plantuml/plantuml/releases/download/v1.2023.12/plantuml-1.2023.12.jar \
    -o /usr/local/bin/plantuml.jar

# Install Structurizr CLI
RUN --mount=type=cache,target=/tmp/downloads \
    mkdir -p /opt/structurizr && \
    STRUCTURIZR_VERSION=$(curl -s https://api.github.com/repos/structurizr/cli/releases/latest | \
    grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' | tr -d 'v') && \
    curl -L "https://github.com/structurizr/cli/releases/download/v${STRUCTURIZR_VERSION}/structurizr-cli.zip" \
    -o /tmp/downloads/structurizr-cli.zip && \
    unzip -q /tmp/downloads/structurizr-cli.zip -d /opt/structurizr && \
    find /opt/structurizr -name "*.sh" -exec chmod +x {} \;

# Install docToolchain
RUN --mount=type=cache,target=/tmp/downloads \
    mkdir -p /opt/doctoolchain && \
    DOCTOOLCHAIN_VERSION=3.4.1 && \
    curl -L "https://github.com/docToolchain/docToolchain/releases/download/v${DOCTOOLCHAIN_VERSION}/docToolchain-${DOCTOOLCHAIN_VERSION}.zip" \
    -o /tmp/downloads/doctoolchain.zip && \
    unzip -q /tmp/downloads/doctoolchain.zip -d /opt/doctoolchain && \
    chmod +x /opt/doctoolchain/docToolchain-${DOCTOOLCHAIN_VERSION}/bin/doctoolchain

# ========================================
# Stage: Docs Runtime
# ========================================
FROM base AS docs

LABEL maintainer="eifel42.dev"
LABEL description="FHS Documentation Builder"
LABEL version="0.3.0"

# Install Java runtime
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    graphviz \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

# Copy tools from builder
COPY --from=docs-builder /usr/local/bin/plantuml.jar /usr/local/bin/plantuml.jar
COPY --from=docs-builder /opt/structurizr /opt/structurizr
COPY --from=docs-builder /opt/doctoolchain /opt/doctoolchain

# Install Python packages for docs
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir pytest pytest-xdist

ENV PATH="/opt/structurizr:/opt/doctoolchain/docToolchain-3.4.1/bin:${PATH}" \
    DTC_HOME="/opt/doctoolchain/docToolchain-3.4.1" \
    LANG=C.UTF-8 \
    JAVA_OPTS="-Xmx16G -Xms4G -XX:+UseG1GC"

CMD ["bash"]

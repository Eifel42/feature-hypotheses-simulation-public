SHELL := /bin/bash
.PHONY: help clean clean-cache clean-docker clean-all test build up check-notebooks down logs format lint execute-notebooks refresh clean-checkpoints docs env-local quality-report quality sonar-tasks sonar-tasks-summary sonar-tasks-lima sonar-tasks-summary-lima

COMPOSE_FILE := cicd/docker-compose.yml
ENV_FILE     := $(if $(wildcard cicd/.env.local),cicd/.env.local,cicd/.env.example)
PROJECT_NAME := $(shell basename $(CURDIR))
DOCKER_IMAGES := cicd-jupyter cicd-docs cicd-docs-builder cicd-docs-test
LIMA_VM      ?= fhs
QUALITY_DIR  := build-output/quality
# Routes to host Docker when available, otherwise starts Lima VM and proxies inside it.
DOCKER       := LIMA_VM=$(LIMA_VM) bash $(CURDIR)/cicd/docker-lima.sh

# Default target
help:
	@echo "Feature Hypotheses Simulation — Mac Host Makefile"
	@echo "====================================================="
	@echo ""
	@echo "All commands run from your Mac. Docker commands automatically"
	@echo "route through Lima VM ($(LIMA_VM)) when needed."
	@echo ""
	@echo "Docker/CI Commands:"
	@echo "  build        Build all Docker images (dev + docs)"
	@echo "  up           Build docs + start full stack (Jupyter + Docs)"
	@echo "  refresh      Reload notebooks, configs & restart containers"
	@echo "  down         Stop all containers"
	@echo "  logs         Show container logs"
	@echo "  test         Run test suite in container"
	@echo "  check-notebooks     Validate all notebooks compile (Docker)"
	@echo "  execute-notebooks   Execute notebooks locally (generates charts)"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         Build arc42 docs with Dagger → docs/html5/"
	@echo ""
	@echo "Quality Gates:"
	@echo "  env-local         Create cicd/.env.local from template"
	@echo "  quality-report    Generate and validate Sonar coverage/test reports without upload"
	@echo "  quality           Run pytest with coverage and SonarScanner against external SonarQube (SONAR_HOST_URL, SONAR_TOKEN)"
	@echo "  sonar-tasks             Pull open SonarQube issues → sonar-agent-tasks.md (grouped by rule)"
	@echo "  sonar-tasks-summary     Print issue counts by rule, no file written"
	@echo "  sonar-tasks-lima        Same as sonar-tasks, runs inside Lima VM ($(LIMA_VM))"
	@echo "  sonar-tasks-summary-lima  Same as sonar-tasks-summary, runs inside Lima VM ($(LIMA_VM))"
	@echo ""
	@echo "Development Commands:"
	@echo "  format       Format code (black + isort)"
	@echo "  lint         Lint code (flake8)"
	@echo "  clean        Remove build artifacts + containers"
	@echo "  clean-docker Clean Docker resources only"
	@echo "  clean-all    Deep clean (build + cache)"
	@echo ""
	@echo "Services:"
	@echo "  Jupyter:  http://localhost:8888  (token: see JUPYTER_TOKEN in cicd/.env.local)"
	@echo "  Docs:     http://localhost:8085"
	@echo ""
	@echo "Lima VM:    $(LIMA_VM) (auto-started when needed)"
	@echo ""

env-local:
	@if [ -f cicd/.env.local ]; then \
		echo "cicd/.env.local already exists"; \
	else \
		cp cicd/.env.example cicd/.env.local; \
		echo "Created cicd/.env.local from template"; \
		echo "Set JUPYTER_TOKEN before running make up"; \
	fi

# == Commands ==

clean-checkpoints:
	@echo "Removing Jupyter checkpoint folders..."
	@find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Checkpoints removed"

clean-cache: clean-checkpoints
	@echo "Removing repository cache directories..."
	@find . \( -path "./.venv" -o -path "./apps/fhs/.venv" \) -prune -o \
		-type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" -o -name ".hypothesis" -o -name ".jupyter_cache" \) \
		-prune -exec rm -rf {} + 2>/dev/null || true
	@find . \( -path "./.venv" -o -path "./apps/fhs/.venv" \) -prune -o -type f \( -name "*.pyc" -o -name ".coverage" \) -delete
	@rm -rf build-output/
	@echo "✓ Repository caches removed"

# Clean build artifacts and Docker resources
clean: clean-docker clean-cache
	@echo "Cleaning Python build artifacts..."
	$(MAKE) -C apps/fhs clean
	@echo "✓ Clean complete"

# Clean only Docker resources (containers, volumes, project images)
clean-docker:
	@echo "Stopping FHS containers..."
	@$(DOCKER) stop fhs-jupyter fhs-docs 2>/dev/null || true
	@echo ""
	@echo "Removing Docker containers and volumes..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down -v --remove-orphans 2>/dev/null || true
	@echo ""
	@echo "Removing Docker volumes..."
	@for vol in $$($(DOCKER) volume ls -q -f name=cicd 2>/dev/null); do \
		$(DOCKER) volume rm $$vol 2>/dev/null || true; \
	done
	@echo ""
	@echo "Removing project Docker images (keeping base images from Docker Hub)..."
	@for img in $(DOCKER_IMAGES); do \
		$(DOCKER) rmi -f $$img 2>/dev/null || true; \
	done
	@echo ""
	@echo "Removing orphaned containers..."
	@$(DOCKER) ps -a -q -f name=fhs 2>/dev/null | grep . && \
		$(DOCKER) ps -a -q -f name=fhs | xargs $(DOCKER) rm -f 2>/dev/null || true
	@$(DOCKER) ps -a -q -f name=cicd 2>/dev/null | grep . && \
		$(DOCKER) ps -a -q -f name=cicd | xargs $(DOCKER) rm -f 2>/dev/null || true
	@echo "✓ Docker cleanup complete"

# Deep clean: everything including build cache
clean-all: clean
	@echo "Removing Docker build cache..."
	@$(DOCKER) builder prune -f 2>/dev/null || true
	@echo ""
	@echo "Removing dangling images..."
	@$(DOCKER) image prune -f 2>/dev/null || true
	@echo "✓ Deep clean complete"

test:
	$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm fhs-dev

build:
	$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev build
	$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile docs build docs-builder docs

up:
	@echo "Cleaning up old containers..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --remove-orphans 2>/dev/null || true
	@echo ""
	@$(MAKE) clean-cache
	@echo ""
	@echo "Building images..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev build jupyter notebook-check
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile docs build docs-builder docs
	@echo ""
	@echo "Compiling notebooks..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm notebook-check || \
		(echo "" && echo "✗ Notebook compilation failed. Aborting." && exit 1)
	@echo ""
	@echo "Building documentation..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile docs up --build --abort-on-container-exit --exit-code-from docs-builder docs-builder || \
		(echo "" && echo "✗ Documentation build failed. Aborting." && exit 1)
	@echo ""
	@echo "Starting FHS stack..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d jupyter docs
	@echo ""
	@echo "✓ Jupyter: http://localhost:8888 (token: see JUPYTER_TOKEN in cicd/.env.local)"
	@echo "✓ Docs:    http://localhost:8085"
	@echo ""

check-notebooks:
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm notebook-check

down:
	$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --remove-orphans

logs:
	$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f

format:
	$(MAKE) -C apps/fhs format

lint:
	$(MAKE) -C apps/fhs lint

quality-report:
	./cicd/run-cicd.sh quality-report

quality:
	./cicd/run-cicd.sh quality

# Pull open SonarQube issues and write AI agent task entries.
# Credentials are read from cicd/.env.local (SONAR_HOST_URL, SONAR_TOKEN).
# Token is never printed; the script loads it internally.
sonar-tasks:
	@echo "Fetching SonarQube issues → sonar-agent-tasks.md"
	@python3 scripts/sonar_to_agent_tasks.py --out sonar-agent-tasks.md
	@echo "✓ sonar-agent-tasks.md ready"

sonar-tasks-summary:
	@echo "SonarQube issue summary (no file written)"
	@python3 scripts/sonar_to_agent_tasks.py --summary

# Run sonar-tasks inside Lima VM (credentials loaded from cicd/.env.local inside the VM).
# Token is never passed on the command line; the script reads it from the mounted env file.
sonar-tasks-lima:
	@command -v limactl >/dev/null 2>&1 || { echo "ERROR: limactl not found. Install: brew install lima"; exit 1; }
	@echo "Fetching SonarQube issues inside Lima VM ($(LIMA_VM)) → sonar-agent-tasks.md"
	@limactl shell $(LIMA_VM) -- bash --login -c 'cd "$(CURDIR)" && python3 scripts/sonar_to_agent_tasks.py --out sonar-agent-tasks.md'
	@echo "✓ sonar-agent-tasks.md ready"

sonar-tasks-summary-lima:
	@command -v limactl >/dev/null 2>&1 || { echo "ERROR: limactl not found. Install: brew install lima"; exit 1; }
	@echo "SonarQube issue summary (Lima VM: $(LIMA_VM))"
	@limactl shell $(LIMA_VM) -- bash --login -c 'cd "$(CURDIR)" && python3 scripts/sonar_to_agent_tasks.py --summary'

execute-notebooks:
	$(MAKE) -C apps/fhs execute-notebooks

# Build arc42 documentation using docker run directly
docs:
	@echo "Building documentation..."
	@mkdir -p docs/html5/images
	@docker run --rm \
		-v "$(CURDIR)/apps/fhs-arc42-doc:/workspace" \
		-v "$(CURDIR)/docs:/build" \
		-w /workspace \
		cicd-docs-builder \
		bash scripts/build-docs.sh || { \
			echo "DocToolchain Docker image not found. Building it..."; \
			docker build -t cicd-docs-builder -f cicd/containers/Dockerfile.docs-builder apps/fhs-arc42-doc/ && \
			docker run --rm \
				-v "$(CURDIR)/apps/fhs-arc42-doc:/workspace" \
				-v "$(CURDIR)/docs:/build" \
				-w /workspace \
				cicd-docs-builder \
				bash scripts/build-docs.sh; \
		}
	@echo ""
	@echo "✓ Docs built: docs/html5/arc42-docs.html"

refresh:
	@echo "Refreshing FHS notebooks and configs..."
	@echo ""
	@echo "1. Stopping running containers..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --remove-orphans 2>/dev/null || true
	@echo ""
	@echo "2. Removing Jupyter checkpoints..."
	@$(MAKE) clean-checkpoints
	@echo ""
	@echo "3. Synchronizing architecture canvas metadata..."
	@python3 apps/fhs-arc42-doc/pipeline/sync_canvas_metadata.py apps/fhs-arc42-doc
	@echo ""
	@echo "4. Validating notebooks..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm notebook-check || \
		(echo "" && echo "✗ Notebook validation failed. Aborting." && exit 1)
	@echo ""
	@echo "5. Restarting Jupyter with fresh configs..."
	@$(DOCKER) compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d jupyter docs
	@echo ""
	@echo "✓ Refresh complete!"
	@echo "✓ Jupyter: http://localhost:8888 (token: see JUPYTER_TOKEN in cicd/.env.local)"
	@echo "✓ Docs:    http://localhost:8085"
	@echo ""
	@echo "All notebooks and configs reloaded. Restart kernel in open notebooks to load changes."
	@echo ""

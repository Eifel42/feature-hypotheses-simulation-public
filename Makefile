SHELL := /bin/bash
.PHONY: help env-local build up down logs test check-notebooks docs-open clean clean-cache clean-docker clean-checkpoints

COMPOSE_FILE := cicd/docker-compose.yml
ENV_FILE     := $(if $(wildcard cicd/.env.local),cicd/.env.local,cicd/.env.example)

help:
	@echo "Feature Hypotheses Simulation — Showcase Makefile"
	@echo "================================================="
	@echo ""
	@echo "Quick start:"
	@echo "  1) make env-local        # create cicd/.env.local from template"
	@echo "  2) edit cicd/.env.local  # set JUPYTER_TOKEN to a random value"
	@echo "  3) make up               # build & start Jupyter + Docs"
	@echo ""
	@echo "Targets:"
	@echo "  build              Build Docker images (Jupyter + Docs server)"
	@echo "  up                 Build, validate notebooks, start the stack"
	@echo "  down               Stop containers"
	@echo "  logs               Tail container logs"
	@echo "  test               Run the FHS test suite in a container"
	@echo "  check-notebooks    Validate that every notebook compiles"
	@echo "  docs-open          Show how to view the prebuilt arc42 docs"
	@echo "  clean              Remove containers and local caches"
	@echo "  clean-docker       Remove project containers, volumes, images"
	@echo "  clean-cache        Remove __pycache__, pytest, ruff caches"
	@echo ""
	@echo "Services after 'make up':"
	@echo "  Jupyter:  http://localhost:8888  (token: see JUPYTER_TOKEN in cicd/.env.local)"
	@echo "  Docs:     http://localhost:8085"

env-local:
	@if [ -f cicd/.env.local ]; then \
		echo "cicd/.env.local already exists"; \
	else \
		cp cicd/.env.example cicd/.env.local; \
		echo "Created cicd/.env.local from template"; \
		echo "Set JUPYTER_TOKEN before running 'make up'"; \
	fi

build:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev build jupyter notebook-check docs

up:
	@echo "Cleaning up old containers..."
	@docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --remove-orphans 2>/dev/null || true
	@echo ""
	@echo "Building images..."
	@docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev build jupyter notebook-check docs
	@echo ""
	@echo "Validating notebooks..."
	@docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm notebook-check || \
		(echo "" && echo "Notebook validation failed. Aborting." && exit 1)
	@echo ""
	@echo "Starting FHS stack..."
	@docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d jupyter docs
	@echo ""
	@echo "Jupyter: http://localhost:8888 (token: see JUPYTER_TOKEN in cicd/.env.local)"
	@echo "Docs:    http://localhost:8085"

down:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down --remove-orphans

logs:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f

test:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm fhs-dev pytest tests/ -v

check-notebooks:
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) --profile dev run --rm notebook-check

docs-open:
	@echo "Prebuilt arc42 documentation:"
	@echo "  docs/html5/arc42-docs.html"
	@echo ""
	@echo "Open it directly in a browser, or run 'make up' to serve at http://localhost:8085."

clean-checkpoints:
	@echo "Removing Jupyter checkpoint folders..."
	@find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} + 2>/dev/null || true

clean-cache: clean-checkpoints
	@echo "Removing repository cache directories..."
	@find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" -o -name ".hypothesis" -o -name ".jupyter_cache" \) -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -type f \( -name "*.pyc" -o -name ".coverage" \) -delete 2>/dev/null || true
	@rm -rf build-output/

clean-docker:
	@echo "Stopping FHS containers..."
	@docker stop fhs-jupyter fhs-docs 2>/dev/null || true
	@echo "Removing containers and volumes..."
	@docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down -v --remove-orphans 2>/dev/null || true

clean: clean-docker clean-cache
	@echo "Clean complete"

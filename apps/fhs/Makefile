# Feature Hypotheses Simulation - Development Makefile
SHELL := /bin/bash

# Auto-activate venv if it exists (prepend venv/bin to PATH for python3, pytest, etc.)
VENV := .venv
ifneq ($(wildcard $(VENV)/bin/python),)
  export PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
  ifneq ($(shell command -v uv 2>/dev/null),)
    PIP := uv pip install --python $(CURDIR)/$(VENV)/bin/python
  else
    PIP := pip install
  endif
else
  PIP := pip install
endif

.PHONY: help install install-dev test test-coverage lint format check ci clean jupyter build execute-notebooks

# Default target
help:
	@echo "Feature Hypotheses Simulation - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  test           Run all tests"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  lint           Run ruff linting"
	@echo "  format         Format code with black and isort"
	@echo "  check          Check formatting without changes"
	@echo "  ci             Full local CI pipeline (format + lint + test + coverage)"
	@echo ""
	@echo "Development:"
	@echo "  clean              Clean build artifacts and cache"
	@echo "  jupyter            Start Jupyter notebook server"
	@echo "  build              Build package for distribution"
	@echo "  execute-notebooks  Execute all notebooks and save outputs (charts)"
	@echo "  docs-api           Generate HTML API docs with pdoc"
	@echo "  docs-api-serve     Serve live API docs at http://localhost:8080"
	@echo ""

# == Setup ==

install:
	$(PIP) -e .

install-dev:
	$(PIP) -e ".[dev]"

# == Testing ==

test:
	python3 -m pytest tests/ -v

test-coverage:
	python3 -m pytest tests/ --cov=src/fhs --cov-branch --cov-report=term-missing --cov-report=html --cov-fail-under=80
	@echo "HTML report: htmlcov/index.html"

# == Code Quality ==

lint:
	python3 -m ruff check src/ tests/

format:
	python3 -m black src/ tests/
	python3 -m isort src/ tests/

check:
	python3 -m black --check src/ tests/
	python3 -m isort --check-only src/ tests/
	python3 -m ruff check src/ tests/

# == CI Pipeline (local) ==

ci: format lint test-coverage
	@echo ""
	@echo "CI pipeline passed: format + lint + tests + coverage"

# == Development ==

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .hypothesis/ .jupyter_cache/ htmlcov/ .coverage build-output/
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -path ./.venv -prune -o -type f -name "*.pyc" -delete

execute-notebooks:
	@echo "Executing all notebooks (generates chart outputs)..."
	@FAILED=0; \
	for nb in $$(find notebooks -name "*.ipynb" -not -path "*/.ipynb_checkpoints/*" -not -name "GLOSSARY.ipynb" -not -name "README.ipynb" | sort); do \
		printf "  %-60s" "$$nb"; \
		if python3 -m nbconvert --to notebook --execute --inplace \
			--ExecutePreprocessor.timeout=300 \
			--ExecutePreprocessor.kernel_name=python3 \
			"$$nb" > /tmp/nbconvert-out.txt 2>&1; then \
			echo "OK"; \
		else \
			echo "FAILED"; \
			head -20 /tmp/nbconvert-out.txt | sed 's/^/    /'; \
			FAILED=1; \
		fi; \
	done; \
	echo ""; \
	if [ "$$FAILED" = "1" ]; then \
		echo "Some notebooks failed. Check output above."; \
		exit 1; \
	fi; \
	echo "Notebook outputs saved (charts are now embedded)."

jupyter:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

build: clean
	$(PIP) build
	python3 -m build

# == API Documentation ==

docs-api:
	@echo "Generating API documentation with pdoc..."
	python3 -m pdoc \
		--output-dir docs-api \
		--html \
		--force \
		fhs fhs.core fhs.application fhs.notebook fhs.presentation.notebook
	@echo "API docs generated: docs-api/index.html"

docs-api-serve:
	@echo "Serving API documentation at http://localhost:8080 ..."
	python3 -m pdoc --port 8080 fhs

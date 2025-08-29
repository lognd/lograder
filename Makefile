.PHONY: all venv build preinstall uninstall reinstall test type lint format check clean

VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip
VENV_PYTEST := $(VENV_DIR)/bin/pytest
VENV_MYPY := $(VENV_DIR)/bin/mypy
VENV_BLACK := $(VENV_DIR)/bin/black
VENV_RUFF := $(VENV_DIR)/bin/ruff
VENV_ISORT := $(VENV_DIR)/bin/isort

all: venv build check test

fast: build check test

venv:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	@test -x "$(VENV_PYTHON)" || python3 -m venv $(VENV_DIR)
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PIP) install --upgrade setuptools

build: clean preinstall uninstall reinstall

preinstall:
	@echo "Installing pre-install dependencies"
	# @$(VENV_PIP) install --upgrade pip setuptools
	@echo "Running pre-install scripts..."

uninstall:
	@echo "Uninstalling ariad..."
	@$(VENV_PIP) uninstall -y ariad || echo "(Already uninstalled)"

reinstall:
	@echo "Installing ariad in editable mode with test extras..."
	@$(VENV_PIP) install -e .[dev]

test:
	@echo "Running tests..."
	@$(VENV_PYTEST) tests/ -q --tb=short --maxfail=5

type:
	@echo "Type-checking with mypy..."
	@$(VENV_MYPY) src

lint:
	@echo "Linting the code..."
	@$(VENV_RUFF) check --fix src tests

format:
	@echo "Checking format with black..."
	@$(VENV_BLACK) src tests

imports:
	@echo "Checking import order with isort..."
	@$(VENV_ISORT) src tests

check: imports lint type format test

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build dist *.egg-info .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find src -type f \( -name '*.so' -o -name '*.pyd' \) -delete
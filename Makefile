VENV := .venv/bin
VENV_PY := $(VENV)/python

ifeq ($(wildcard $(VENV_PY)),)
PYTHON := python3
PIP := pip3
BLACK := black
RUFF := ruff
MYPY := mypy
ISORT := isort
PYTEST := pytest
else
PYTHON := $(VENV_PY)
PIP := $(VENV)/pip3
BLACK := $(VENV)/black
RUFF := $(VENV)/ruff
MYPY := $(VENV)/mypy
ISORT := $(VENV)/isort
PYTEST := $(VENV)/pytest
endif

APROG_PUBLIC  := ../aprog-public
APROG_PRIVATE := ../aprog-private

.PHONY: check build uninstall all test test-companions self-esteem

all: uninstall build check test

uninstall:
	@$(PIP) uninstall -y lograder

build:
	@$(PIP) install -e .[dev]

check:
	@$(BLACK) src/ tests/
	@$(RUFF) format src/ tests/
	@$(RUFF) check src/ tests/ --fix
	@$(ISORT) src/ tests/
	@$(MYPY) --config-file mypy-py310.ini src/ tests/
	@$(MYPY) --config-file mypy-py314.ini src/ tests/

version:
	@$(PYTHON) --version
	@$(PIP) --version
	@$(PYTEST) --version
	@$(BLACK) --version
	@$(RUFF) --version
	@$(ISORT) --version
	@$(MYPY) --version

test:
	@$(PYTEST)

test-verbose:
	@$(PYTEST) -v -s

test-fast:
	@$(PYTEST) -m "not slow"

test-verbose-fast:
	@$(PYTEST) -v -s -m "not slow"

test-companions:
	@if [ -f "$(APROG_PUBLIC)/Makefile" ]; then \
		echo "--- aprog-public tests ---"; \
		$(MAKE) -C $(APROG_PUBLIC) test-all; \
	else \
		echo "aprog-public not found, skipping"; \
	fi
	@if [ -f "$(APROG_PRIVATE)/pyproject.toml" ]; then \
		echo "--- aprog-private tests ---"; \
		cd $(APROG_PRIVATE) && (.venv/bin/pytest -m "not slow" 2>/dev/null || pytest -m "not slow"); \
		code=$$?; [ $$code -eq 0 ] || [ $$code -eq 5 ] || exit $$code; \
	else \
		echo "aprog-private not found, skipping"; \
	fi

self-esteem:
	@cloc --vcs=git src/
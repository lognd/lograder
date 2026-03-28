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

.PHONY: check build uninstall all test self-esteem

all: uninstall build check test

uninstall:
	@$(PIP) uninstall -y lograder

build:
	@$(PIP) install -e .[dev]

check:
	@$(BLACK) src/ tests/
	@$(RUFF) format src/ tests/
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

self-esteem:
	@cloc --vcs=git src/
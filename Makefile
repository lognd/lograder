VENV := .venv/bin
VENV_PY := $(VENV)/python

ifeq ($(wildcard $(VENV_PY)),)
PYTHON := python3
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
	@$(MYPY) src/ tests/

test:
	@$(PYTEST)

test-verbose:
	@$(PYTEST) -v -s

self-esteem:
	@cloc --vcs=git .
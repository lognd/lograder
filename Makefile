APROG_PUBLIC  := ../aprog-public
APROG_PRIVATE := ../aprog-private

.PHONY: install build uninstall all test test-verbose test-fast test-verbose-fast \
        test-companions lint fmt typecheck check version self-esteem clean upload

all: uninstall build check test

install:
	@uv sync --extra dev

build: install

uninstall:
	@uv pip uninstall -y lograder

lint:
	@uv run ruff check src/ tests/

fmt:
	@uv run ruff format src/ tests/
	@uv run ruff check src/ tests/ --fix

typecheck:
	@uv run ty check src/

check: fmt lint typecheck test

version:
	@uv run python --version
	@uv --version
	@uv run pytest --version
	@uv run ruff --version
	@uv run ty --version

test:
	@uv run pytest -n auto

test-verbose:
	@uv run pytest -v -s

test-fast:
	@uv run pytest -n auto -m "not slow"

test-verbose-fast:
	@uv run pytest -v -s -m "not slow"

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

clean:
	rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ .testmondata
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null; true

upload: clean
	@set -a && . ./.env && set +a; \
	NEW=$$(uv run python scripts/bump_version.py); \
	git add pyproject.toml; \
	git commit -m "chore: bump version to $$NEW"; \
	git push; \
	uv build && uv publish
